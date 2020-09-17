import os

import boto3
from celery import shared_task
from django.conf import settings
from django.utils.crypto import get_random_string
from playwright import sync_playwright

from collab_app.models import (
    Task
)


@shared_task
def create_screenshots_for_task(task_id, html, browser_name, device_scale_factor, window_width, window_height):
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
