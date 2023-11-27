import datetime

from botocore.client import BaseClient
from sqlalchemy import Table, update
from sqlalchemy.orm import Session

import configuration
from notification import Notification


def update_notification(header: str, data: Notification, session: Session, s3: BaseClient, table: Table):
    """
    ECS 에 이미 크롤링 된 데이터가 존재 한다면 이를 업데이트 하고, 아니라면 새로 생성하는 함수

    :param header: s3에 저장될 content 파일 명 앞에 붙을 header
    :param data: 새로 크롤링한 데이터
    :param session: ecs에 연결된 session
    :param s3: s3에 연결된 Client
    :param table: notice table 구조로 이루어진 table

    """
    prev_row = session.execute(
        table.select()
        .where(table.c.title == data.title)
    ).first()
    if prev_row is None:
        file_path = ("{0}notice/{1}".format(configuration.file_path, header)
                     + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") + ".txt")

        s3.put_object(
            Body=data.content,
            Bucket=configuration.bucket_name,
            Key=file_path
        )

        data.content = "https://{0}.s3.amazonaws.com/".format(configuration.bucket_name) + file_path
        session.add(data)
    else:
        if data.views != prev_row.views:
            session.execute(
                update(table)
                .where(table.c.title == data.title)
                .values(views=data.views))
        file_link: str = prev_row.content
        header_len = len("https://{0}.s3.amazonaws.com/".format(configuration.bucket_name))
        file_path = file_link[header_len:]
        content_streaming_body = s3.get_object(
            Bucket=configuration.bucket_name,
            Key=file_path,
            ResponseContentEncoding="utf-8",
        )['Body']
        previous_content: bytes = content_streaming_body.read()
        decoded_previous_content: str = previous_content.decode('utf-8')

        if data.content != decoded_previous_content:
            s3.put_object(
                Body=data.content,
                Bucket=configuration.bucket_name,
                Key=file_path
            )
            current_datetime = datetime.datetime.now()
            session.execute(
                update(table)
                .where(table.c.title == data.title)
                .values(updated_at=current_datetime)
            )
            print("success updating content")

        if data.image_url != prev_row.image_url:
            session.execute(
                update(table)
                .where(table.c.title == data.title)
                .values(image_url=data.image_url)
            )

        content_streaming_body.close()
