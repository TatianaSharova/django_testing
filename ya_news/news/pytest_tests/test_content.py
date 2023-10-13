import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_news_count(all_news, home_url, client):
    """Количество новостей на главной странице — не более 10."""
    response = client.get(home_url)
    object_list = response.context['object_list']
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(all_news, home_url, client):
    """Новости отсортированы от самой свежей к самой старой."""
    response = client.get(home_url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


def test_comments_order(news, comments, client):
    """
    Комментарии на странице отдельной новости отсортированы

    в хронологическом порядке: старые в начале списка, новые — в конце.
    """
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert ('news' in response.context) is True
    news = response.context['news']
    comments = news.comment_set.all()
    assert comments[0].created < comments[1].created


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('client'), False),
        (pytest.lazy_fixture('author_client'), True),
    ),
)
def test_pages_contains_form(news, parametrized_client, expected_status):
    """
    Анонимному пользователю недоступна форма для отправки комментария

    на странице отдельной новости, а авторизованному доступна.
    """
    url = reverse('news:detail', args=(news.id,))
    response = parametrized_client.get(url)
    assert ('form' in response.context) is expected_status
