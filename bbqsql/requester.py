from .query import Query
from . import debug

from copy import copy
from time import time

import requests


class Requester(object):
    @debug.func
    def __init__( self , request , send_request_function ):
        self.request = request
        self.send_request_function = send_request_function
    
    @debug.func
    def make_request(self,value=""):
        new_request = copy(self.request)
        #iterate over the __dict__ of the request and compile any elements that are 
        #query objects.
        for elt in [q for q in new_request.__dict__ if isinstance(new_request.__dict__[q],Query)]:
            opts = new_request.__dict__[elt].get_options()
            for opt in opts:
                opts[opt] = value
            new_request.__dict__[elt].set_options(opts)
            new_request.__dict__[elt] = new_request.__dict__[elt].render()
        
        #the function we are going to call
        function_to_call = self.send_request_function
        #if the function they sent us is a string, we will get that attr from the request and call it
        #with the args and kwargs passed to us.
        if type(self.send_request_function) == str:
            function_to_call = getattr(new_request,self.send_request_function)
            args = []
        #otherwise we will send new_request as the first argument to self.send_request_function
        else:
            args = [new_request]

        if not hasattr(function_to_call,"__call__"):
            raise Exception('the send_request_function you passed to Requester doesnt exist in the request object you passed')

        response = function_to_call(*args)
        
        return response


def requests_send(request):
    '''out send_request_function. we need this because the requests library doesn't have a 
    good way to build a response without sending it and then send it having a response returned
    as opposed to a bool'''
    if request.send():
        return request.response
    else:
        raise         

def requests_time_pre_hook(request):
    #hooks for the requests module
    request.start_time = time()
    return request

def requests_time_post_hook(request):
    #hooks for the requests module
    request.response.response_time = time() - request.start_time
    return request


class HTTPRequester(Requester):
    '''A Requester object built ontop of the requests library. This is capable of
    doing HTTP/HTTPS. This object is intentionally pretty limited. If you want to do
    any crazy requests you should use the plain old bbqsql.Requester object. This
    object just abstracts away some of the tedious stuff for the base case...'''

    @debug.func
    def __init__(self,url,method='GET',data = None,send_request_function=requests_send):
        #build a requests.Session object to hold settings
        session = requests.Session()
        #build a request object (but don't send it)
        request = session.request(url=url,method=method,data=data,return_response=False,hooks = {'pre_request':requests_time_pre_hook,'post_request':requests_time_post_hook})

        super(HTTPRequester,self).__init__(request, send_request_function)
    