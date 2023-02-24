from django.conf import settings

def nalypoll_gtag(request):
    return {
        'NALYPOLL_GTAG': settings.NALYPOLL_GTAG,
    }
