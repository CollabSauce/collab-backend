import os
import re

import boto3
from celery import shared_task
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from playwright import sync_playwright

from collab_app.models import (
    Task,
    TaskComment,
    User
)
from collab_app.utils import (
    send_email
)


@shared_task
def create_screenshots_for_task(task_id, html, browser_name, device_scale_factor, window_width, window_height):
    print('create_screenshots_for_task')
    task = Task.objects.get(id=task_id)
    project = task.project
    organization = project.organization

    file_key = get_random_string(length=32)
    window_screenshot_filepath = f'tmp/{file_key}-window.png'
    element_screenshot_filepath = f'tmp/{file_key}-element.png'

    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    with sync_playwright() as p:
        lower_bname = browser_name.lower()
        if lower_bname == 'chrome':
            chosen_browser = p.chromium
        elif lower_bname == 'safari':
            chosen_browser = p.webkit
        elif lower_bname == 'firefox':
            chosen_browser = p.firefox
        else:
            chosen_browser = p.chromium  # not a chrome/safari/firefox browser. default to chrome

        browser = chosen_browser.launch()
        page = browser.newPage(deviceScaleFactor=device_scale_factor)
        page.setViewportSize(width=window_width, height=window_height)
        page.setContent(html)
        # disable all scripts: https://stackoverflow.com/a/51953118/9711626
        page.evaluate('document.body.innerHTML = document.body.innerHTML')

        # TODO: data-collab-manual-height ???
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
            document.getElementById('collab-sauce-iframe').style.display = 'none';
            document.querySelector('.CollabSauce__outline__').classList.remove('CollabSauce__outline__')
        }''')
        page.screenshot(path=window_screenshot_filepath, type='png')
        element = page.querySelector('[data-collab-selected-element]')
        element.screenshot(path=element_screenshot_filepath, type='png')
        browser.close()

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
        os.remove(element_screenshot_filepath)
    except Exception as err:
        print('Error while deleting files')
        print(err)

    task.window_screenshot_url = f'https://s3-us-west-1.amazonaws.com/{s3_bucket}/{window_file_name}'
    task.element_screenshot_url = f'https://s3-us-west-1.amazonaws.com/{s3_bucket}/{element_file_name}'
    task.save()


@shared_task
def notify_participants_of_task(task_id):
    task = Task.objects.get(id=task_id)
    task_creator_name = f'{task.creator.first_name} {task.creator.last_name}'

    # match the id from `@@@__<ID HERE>^^^Some Name@@@^^^`
    regex = r'@@@__(\d+)\^\^\^'
    matches = re.findall(regex, task.title)
    for user_id in matches:
        try:
            mentioned = User.objects.get(id=user_id)
            subject = f'{task_creator_name} has mentioned you on a task.'
            body = render_to_string('emails/tasks/task-mention.html', {
                'task_creator_name': task_creator_name,
                'task_url': f'https://app.collabsauce.com/projects/{task.project.id}/tasks/{task_id}'
            })
            send_email(subject, body, 'info@collabsauce.com', [mentioned.email], fail_silently=True)
        except Exception as err:
            print('Error while notifying on task create')
            print(err)


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
                'task_url': f'https://app.collabsauce.com/projects/{project_id}/tasks/{task.id}'
            })
            send_email(subject, body, 'info@collabsauce.com', [mentioned.email], fail_silently=True)
            already_mentioned.add(mentioned)
        except Exception as err:
            print('Error while notifying on task comment create')
            print(err)

    # Now notify everyone who is 'participating' on the task chain
    users_to_notify = [task.creator]  # notify the task creator
    for comment in task.task_comments.all():
        users_to_notify.append(comment.creator)  # notify the task-comment creator
        matches = re.findall(regex, comment.text)
        for user_id in matches:
            mentioned = User.objects.get(id=user_id)
            users_to_notify.append(mentioned)  # notify anyone who has been previously mentioned on a task

    for user in users_to_notify:
        if user not in already_mentioned:
            try:
                subject = f'{taskcomment_creator_name} has commented on a task you are participating on.'
                body = render_to_string('emails/tasks/taskcomment-participating.html', {
                    'taskcomment_creator_name': taskcomment_creator_name,
                    'task_url': f'https://app.collabsauce.com/projects/{project_id}/tasks/{task.id}'
                })
                send_email(subject, body, 'info@collabsauce.com', [user.email], fail_silently=True)
                already_mentioned.add(user)
            except Exception as err:
                print('Error while notifying on task comment notify all create')
                print(err)
