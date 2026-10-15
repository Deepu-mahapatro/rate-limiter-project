
from django.urls import path
from .views import test_rate_limit, test_token_bucket, test_sliding_window, test_sliding_window_log, test_leaky_bucket

urlpatterns = [
    # API endpoint for testing fixed window 
    path("test/", test_rate_limit, name="test_rate_limit"),
    
    #API endpoint for testing token bucket 
    path("token-bucket/", test_token_bucket, name="test_token_bucket"),

    #API endpoint for testing sliding window counter 
    path("sliding-window/", test_sliding_window, name="test_sliding_window"),
    
    #API endpoint for testing sliding window log 
    path("sliding-window-log/", test_sliding_window_log, name="test_sliding_window_log"),
    
    #API endpoint for testing leaky bucket 
    path("leaky-bucket/", test_leaky_bucket, name="test_leaky_bucket"),
    ]
