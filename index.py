from app import app

#for vercel
def handler(request):
    with app.test_request_context(
        path=request.path,
        method=request.method,
        headers=request.headers,
        data=request.get_data()
    ):
        return app.full_dispatch_request()