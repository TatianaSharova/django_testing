from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import WARNING
from news.models import Comment


def test_user_can_create_comment(
        author_client, author, news, comment_form_data, detail_url
):
    """Авторизованный пользователь может отправить комментарий."""
    comments_count = Comment.objects.count()
    assert comments_count == 0
    response = author_client.post(detail_url, data=comment_form_data)
    assertRedirects(response, f'{detail_url}#comments')
    assert Comment.objects.count() != comments_count
    new_comment = Comment.objects.get(
        text=comment_form_data['text'],
        news=news, author=author)
    assert new_comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    comment_form_data, client, detail_url
):
    """Анонимный пользователь не может отправить комментарий."""
    comments_count = Comment.objects.count()
    client.post(detail_url, data=comment_form_data)
    comments_count_after = Comment.objects.count()
    assert comments_count == comments_count_after


def test_user_cant_use_bad_words(bad_words_data, author_client, detail_url):
    """
    Если комментарий содержит запрещённые слова,

    он не будет опубликован, а форма вернёт ошибку.
    """
    response = author_client.post(detail_url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(
        author_client, comment_id_for_args, detail_url
):
    """Авторизованный пользователь может удалять свои комментарии."""
    url = reverse('news:delete', args=comment_id_for_args)
    comments_count = Comment.objects.count()
    assert comments_count == 1
    response = author_client.delete(url)
    url_to_comments = detail_url + '#comments'
    assertRedirects(response, url_to_comments)
    comments_count_after = Comment.objects.count()
    assert comments_count != comments_count_after


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(
        comment_id_for_args, admin_client,
):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    comments_count = Comment.objects.count()
    url = reverse('news:delete', args=comment_id_for_args)
    response = admin_client.delete(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count_after = Comment.objects.count()
    assert comments_count == comments_count_after


def test_author_can_edit_comment(
        author_client, comment_id_for_args, detail_url,
        comment_form_data, comment
):
    """Авторизованный пользователь может редактировать свои комментарии."""
    url = reverse('news:edit', args=comment_id_for_args)
    response = author_client.post(url, data=comment_form_data)
    url_to_comments = detail_url + '#comments'
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == comment_form_data['text']


def test_user_cant_edit_comment_of_another_user(
        admin_client, comment_id_for_args, comment_form_data, comment
):
    """
    Авторизованный пользователь не может

    редактировать чужие комментарии.
    """
    url = reverse('news:edit', args=comment_id_for_args)
    response = admin_client.post(url, data=comment_form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text
