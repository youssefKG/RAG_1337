from django.http import HttpResponse, HttpRequest

def index(request: HttpRequest) -> HttpResponse:
    print("rquest", request)
    return HttpResponse("hello world")
