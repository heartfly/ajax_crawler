#coding=utf8
from scrapy.http import Request, FormRequest, HtmlResponse
from threading import Thread, Event
import gtk
import webkit
import jswebkit
import urlparse

class Render(object):
    pending = Event()
    def __init__(self, request, response):
        try:
            print 'Render.__init__'
            self.webview = webkit.WebView()
            self.webview.connect( 'load-finished', self.load_finished )
            parsed_url = urlparse.urlparse(request.url)
            self.webview.load_html_string(response.body, parsed_url.scheme+'://'+parsed_url.netloc)
            #self.webview.load_uri(request.url)
        except Exception,e:
            print e
        finally:
            gtk.main()


    def load_finished(self, *args, **kw):
        try:
            print 'Render.load_finished'
            js = jswebkit.JSContext( self.webview.get_main_frame().get_global_context() )
            self.rendered_html = str( js.EvaluateScript( 'document.body.innerHTML' ) )
            self.pending.set()
        except Exception,e:
            print e
        finally:
            gtk.main_quit()

class WebkitDownloader(object):
    def process_response(self, request, response, spider):
        try:
            render = Render(request, response)
            render.pending.wait()
            response = response.replace(body = render.rendered_html)
        except Exception,e:
            print e
        return response

    #def process_request( self, request, spider ):
        #webview = webkit.WebView()
        #webview.connect( 'load-finished', lambda v,f: gtk.main_quit() )
        #webview.load_uri( request.url )
        #gtk.main()
        #js = jswebkit.JSContext( webview.get_main_frame().get_global_context() )
        #renderedBody = str( js.EvaluateScript( 'document.body.innerHTML' ) )
        #return HtmlResponse( request.url, body=renderedBody )
