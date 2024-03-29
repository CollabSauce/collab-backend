import base64
import os
import logging
import re

import boto3
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from playwright import sync_playwright
from sentry_sdk import capture_exception

from collab_app.models import (
    Task,
    TaskColumn,
    TaskComment,
    TaskDataUrl,
    TaskHtml,
    User
)
from collab_app.utils import (
    send_email
)

logger = logging.getLogger('collabsauce')


@shared_task
def create_screenshots_for_task(task_id, task_html_id, browser_name, device_scale_factor, window_width, window_height):
    task = Task.objects.get(id=task_id)
    task_html = TaskHtml.objects.get(id=task_html_id)
    html = task_html.html

    file_key, window_screenshot_filepath, element_screenshot_filepath = get_filekey_and_filepaths()

    with sync_playwright() as p:
        lower_bname = browser_name.lower()
        if lower_bname == 'chrome':
            chosen_browser = p.chromium
        elif lower_bname == 'safari':
            # chosen_browser = p.webkit
            chosen_browser = p.chromium  # Bug with safari still :/. Not loading correct libs on install :/.
        elif lower_bname == 'firefox':
            chosen_browser = p.firefox  # Note: inputs not rendered 100%. fix later?
        else:
            chosen_browser = p.chromium  # not a chrome/safari/firefox browser. default to chrome

        # need chromiumSandbox=False because we are not a ROOT user
        # See this answer: https://stackoverflow.com/a/50107359/9711626 for `args` arguments.
        browser = chosen_browser.launch(chromiumSandbox=False)
        page = browser.newPage(deviceScaleFactor=device_scale_factor)
        page.setViewportSize(width=window_width, height=window_height)
        page.setContent(html)
        # disable all scripts: https://stackoverflow.com/a/51953118/9711626
        # TODO: THIS ISN'T WORKING AS EXPECTED. comment out and find a different solution (if needed?)
        # page.evaluate('document.body.innerHTML = document.body.innerHTML')

        # TODO: data-collab-manual-height ???
        # TODO: get checkboxes working on firefox ???

        page.evaluate('''() => {
            document.querySelectorAll('[data-collab-checked="true"').forEach(el => el.checked = true);
            document.querySelectorAll('[data-collab-top]').forEach(el => {
                var element = el;
                var scrollYAmount = el.getAttribute('data-collab-top');
                if (el.tagName.toLowerCase() === 'body') {
                    element = window;
                }
                element.scrollBy(0, scrollYAmount)
            });
            document.querySelectorAll('[data-collab-left]').forEach(el => {
                var element = el;
                var scrollXAmount = el.getAttribute('data-collab-left');
                if (el.tagName.toLowerCase() === 'body') {
                    element = window;
                }
                element.scrollBy(scrollXAmount, 0)
            });
            document.querySelectorAll('[data-collab-value]').forEach(el => {
                var val = el.getAttribute('data-collab-value');
                el.value = val;
            });
            document.querySelectorAll('[data-collab-checked]').forEach(el => {
                el.checked = true;
            });
            document.getElementById('collab-sauce-iframe').style.display = 'none';
            document.querySelectorAll('.collabsauce-tick-ruler').forEach(el => {
                el.style.display = 'none';
            });
            document.querySelectorAll('.collabsauce-ruler-top-corner').forEach(el => {
                el.style.display = 'none';
            });
            document.querySelectorAll('.collabsauce-web-paint-toolbar').forEach(el => {
                el.style.display = 'none';
            });
            document.querySelector('.CollabSauce__outline__') &&
                document.querySelector('.CollabSauce__outline__').classList.remove('CollabSauce__outline__');
            document.querySelectorAll('[collabsauce-href]').forEach(el => {
                el.href = el.getAttribute('collabsauce-href');
            });
            document.querySelectorAll('[collabsauce-src]').forEach(el => {
                el.src = el.getAttribute('collabsauce-src');
            });
        }''')
        # we need to do this because the collabsauce-href's are technically loaded after the "load" event.
        # so we want to wait for that styling be loaded
        page.waitForLoadState('networkidle')
        # wait 2 extra seconds just incase
        page.waitForTimeout(2000)
        page.screenshot(path=window_screenshot_filepath, type='png')
        if task.has_target:
            page.waitForSelector('[data-collab-selected-element]');
            element = page.querySelector('[data-collab-selected-element]')
            element.screenshot(path=element_screenshot_filepath, type='png')
        browser.close()

    upload_screenshots(task, file_key, window_screenshot_filepath, element_screenshot_filepath)
    task_html.delete()


@shared_task
def upload_chrome_extension_screenshots_for_task(task_id, task_data_url_id):
    task = Task.objects.get(id=task_id)
    task_data_url = TaskDataUrl.objects.get(id=task_data_url_id)
    window_screenshot_data_url = task_data_url.window_screenshot_data_url
    element_screenshot_data_url = task_data_url.element_screenshot_data_url

    file_key, window_screenshot_filepath, element_screenshot_filepath = get_filekey_and_filepaths()

    with open(window_screenshot_filepath, 'wb') as f:
        f.write(base64.b64decode(re.sub('data:image/png;base64,', '', window_screenshot_data_url)))

    if task.has_target:
        with open(element_screenshot_filepath, 'wb') as f:
            f.write(base64.b64decode(re.sub('data:image/png;base64,', '', element_screenshot_data_url)))

    upload_screenshots(task, file_key, window_screenshot_filepath, element_screenshot_filepath)
    task_data_url.delete()


def get_filekey_and_filepaths():
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    file_key = get_random_string(length=32)
    window_screenshot_filepath = f'tmp/{file_key}-window.png'
    element_screenshot_filepath = f'tmp/{file_key}-element.png'
    return file_key, window_screenshot_filepath, element_screenshot_filepath


def upload_screenshots(task, file_key, window_screenshot_filepath, element_screenshot_filepath):
    project = task.project
    organization = project.organization

    s3 = boto3.resource('s3')
    s3_bucket = getattr(settings, 'S3_BUCKET')
    window_file_name = f'{organization.id}/{project.id}/{file_key}-window.png'
    element_file_name = f'{organization.id}/{project.id}/{file_key}-element.png'
    s3.meta.client.upload_file(
        Filename=window_screenshot_filepath,
        Bucket=s3_bucket,
        Key=window_file_name,
        ExtraArgs={
            'ContentType': 'image/png'
        }
    )
    if task.has_target:
        s3.meta.client.upload_file(
            Filename=element_screenshot_filepath,
            Bucket=s3_bucket,
            Key=element_file_name,
            ExtraArgs={
                'ContentType': 'image/png'
            }
        )

    try:
        os.remove(window_screenshot_filepath)
        if task.has_target:
            os.remove(element_screenshot_filepath)
    except Exception as err:
        logger.info('Error while deleting files')
        capture_exception(err)
        logger.info(err)

    task.window_screenshot_url = f'https://s3-{settings.AWS_REGION}.amazonaws.com/{s3_bucket}/{window_file_name}'
    if task.has_target:
        task.element_screenshot_url = f'https://s3-{settings.AWS_REGION}.amazonaws.com/{s3_bucket}/{element_file_name}'
    task.save()


@shared_task
def notify_participants_of_task(task_id):
    task = Task.objects.get(id=task_id)
    if task.creator:
        task_creator_name = f'{task.creator.first_name} {task.creator.last_name}'
    else:
        task_creator_name = task.one_off_email_set_by
    project_id = task.project.id

    already_mentioned = set()

    # Notify the person assigned on the task (if applicable)
    assignee = task.assigned_to
    if assignee:
        try:
            subject = f'{task_creator_name} has assigned you a task.'
            body = render_to_string('emails/tasks/task-assigned.html', {
                'task_creator_name': task_creator_name,
                'task_url': f'projects/{project_id}/tasks/{task_id}'
            })
            send_email(subject, body, settings.EMAIL_HOST_USER, [assignee.email], fail_silently=False)
            already_mentioned.add(assignee)
        except Exception as err:
            logger.info('Error while notifying assignee on task create')
            capture_exception(err)
            logger.info(err)

    # match the id from `@@@__<ID HERE>^^^Some Name@@@^^^`

    # Notify the people mentioned on the comment.
    regex = r'@@@__(\d+)\^\^\^'
    matches = re.findall(regex, task.title)
    for user_id in matches:
        try:
            mentioned = User.objects.get(id=user_id)
            if mentioned not in already_mentioned:
                subject = f'{task_creator_name} has mentioned you on a task.'
                body = render_to_string('emails/tasks/task-mention.html', {
                    'task_creator_name': task_creator_name,
                    'task_url': f'projects/{project_id}/tasks/{task_id}'
                })
                send_email(subject, body, settings.EMAIL_HOST_USER, [mentioned.email], fail_silently=False)
                already_mentioned.add(mentioned)
        except Exception as err:
            logger.info('Error while notifying on task create')
            capture_exception(err)
            logger.info(err)


@shared_task
def notify_participants_of_task_comment(task_comment_id):
    task_comment = TaskComment.objects.get(id=task_comment_id)
    task = task_comment.task
    task_comment_creator = task_comment.creator
    taskcomment_creator_name = f'{task_comment_creator.first_name} {task_comment_creator.last_name}'
    project_id = task.project.id

    already_mentioned = set([task_comment_creator])

    # match the id from `@@@__<ID HERE>^^^Some Name@@@^^^`

    # Notify the people mentioned on the comment.
    regex = r'@@@__(\d+)\^\^\^'
    matches = re.findall(regex, task_comment.text)
    for user_id in matches:
        try:
            mentioned = User.objects.get(id=user_id)
            subject = f'{taskcomment_creator_name} has mentioned you on a task.'
            body = render_to_string('emails/tasks/taskcomment-mention.html', {
                'taskcomment_creator_name': taskcomment_creator_name,
                'task_url': f'projects/{project_id}/tasks/{task.id}'
            })
            send_email(subject, body, settings.EMAIL_HOST_USER, [mentioned.email], fail_silently=False)
            already_mentioned.add(mentioned)
        except Exception as err:
            logger.info('Error while notifying on task comment create')
            capture_exception(err)
            logger.info(err)

    # notify the task creator and task.assigned_to . If they are the same person, logic below already handles duplicates
    users_to_notify = [task.creator, task.assigned_to]

    # Now notify everyone who is 'participating' on the task chain
    for comment in task.task_comments.all():
        users_to_notify.append(comment.creator)  # notify the task-comment creator
        matches = re.findall(regex, comment.text)
        for user_id in matches:
            mentioned = User.objects.get(id=user_id)
            users_to_notify.append(mentioned)  # notify anyone who has been previously mentioned on a task

    # check the task.title too
    matches = re.findall(regex, task.title)
    for user_id in matches:
        mentioned = User.objects.get(id=user_id)
        users_to_notify.append(mentioned)  # notify anyone who has been mentioned on the task title

    for user in users_to_notify:
        if user and user not in already_mentioned:
            try:
                subject = f'{taskcomment_creator_name} has commented on a task you are participating on.'
                body = render_to_string('emails/tasks/taskcomment-participating.html', {
                    'taskcomment_creator_name': taskcomment_creator_name,
                    'task_url': f'projects/{project_id}/tasks/{task.id}'
                })
                send_email(subject, body, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
                already_mentioned.add(user)
            except Exception as err:
                logger.info('Error while notifying on task comment notify all create')
                capture_exception(err)
                logger.info(err)


@shared_task
def notify_participants_of_assignee_change(task_id):
    # TODO: notify original_assignee (if there was one) that they are unassigned??
    task = Task.objects.get(id=task_id)

    assignee = task.assigned_to
    try:
        subject = 'You have been assigned a task!'
        body = render_to_string('emails/tasks/task-assigned-changed.html', {
            'task_url': f'projects/{task.project.id}/tasks/{task_id}'
        })
        send_email(subject, body, settings.EMAIL_HOST_USER, [assignee.email], fail_silently=False)
    except Exception as err:
        logger.info('Error while notifying assignee on task update')
        capture_exception(err)
        logger.info(err)


@shared_task
def notify_participants_of_task_column_change(task_id, prev_task_column_id, new_task_column_id, mover_id):
    task = Task.objects.get(id=task_id)
    prev_task_column = TaskColumn.objects.get(id=prev_task_column_id)
    new_task_column = TaskColumn.objects.get(id=new_task_column_id)
    mover = User.objects.get(id=mover_id)
    mover_full_name = f'{mover.first_name} {mover.last_name}'
    project_id = task.project.id

    # notify the task creator and task.assigned_to.
    # If they are the same person, or if that was the mover, logic below already handles duplicates
    users_to_notify = [task.creator, task.assigned_to]

    # Now notify everyone who is 'participating' on the task chain
    regex = r'@@@__(\d+)\^\^\^'
    for comment in task.task_comments.all():
        users_to_notify.append(comment.creator)  # notify the task-comment creator
        matches = re.findall(regex, comment.text)
        for user_id in matches:
            mentioned = User.objects.get(id=user_id)
            users_to_notify.append(mentioned)  # notify anyone who has been previously mentioned on a task

    # check the task.title too
    matches = re.findall(regex, task.title)
    for user_id in matches:
        mentioned = User.objects.get(id=user_id)
        users_to_notify.append(mentioned)  # notify anyone who has been mentioned on the task title

    already_mentioned = set([mover])

    for user in users_to_notify:
        if user and user not in already_mentioned:
            try:
                subject = (
                    f'{mover_full_name} has moved task # {task.task_number} '
                    f'from `{prev_task_column.name}` to `{new_task_column.name}`.'
                )
                body = render_to_string('emails/tasks/task-moved-column.html', {
                    'mover_full_name': mover_full_name,
                    'task_number': task.task_number,
                    'prev_task_column_name': prev_task_column.name,
                    'new_task_column_name': new_task_column.name,
                    'task_url': f'projects/{project_id}/tasks/{task.id}'
                })
                send_email(subject, body, settings.EMAIL_HOST_USER, [user.email], fail_silently=False)
                already_mentioned.add(user)
            except Exception as err:
                logger.info('Error while notifying on task move notify all')
                capture_exception(err)
                logger.info(err)
