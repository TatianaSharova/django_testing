from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from news.forms import BAD_WORDS
from news.models import Comment, News


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def news():
    news = News.objects.create(title='Заголовок', text='Текст')
    return news


@pytest.fixture
def comment(news, author):
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария'
    )
    return comment


@pytest.fixture
def news_id_for_args(news):
    return news.id,


@pytest.fixture
def comment_id_for_args(comment):
    return comment.id,


@pytest.fixture
def today():
    today = datetime.today()
    return today


@pytest.fixture
def all_news(today):
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def comments(news, author):
    now = timezone.now()
    for index in range(2):
        comments = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comments.created = now + timedelta(days=index)
        comments.save()


@pytest.fixture
def comment_form_data():
    return {
        'text': 'Текст комментария',
    }


@pytest.fixture
def home_url():
    home_url = reverse('news:home')
    return home_url


@pytest.fixture
def bad_words_data():
    return {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}


@pytest.fixture
def detail_url(news):
    return reverse('news:detail', args=(news.id,))
