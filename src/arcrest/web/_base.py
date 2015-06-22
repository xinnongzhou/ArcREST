"""
   Base Class that all class that perform
   web operations will inherit from.
"""
import gzip
import os
import urllib
import urllib2
import json
import mimetypes
import mimetools
from cStringIO import StringIO
import re
try:
    import requests
    allowRequests = True
except:
    allowRequests = False
class AGOLRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

class BaseWebOperations(object):
    """ base class that holds all the common web request operations """
    _referer_url = None
    _useragent = "ArcREST"
    _proxy_url = None
    _proxy_port = None

    def _do_get():
        pass
    #----------------------------------------------------------------------
    def _do_get_stnd(self, url, param_dict,
                     handler=None, cookiejar=None,
                     header=None, proxy_url=None,
                     proxy_port=None,compress=True):
        """ performs a get operation """
        handlers = []
        headers = [('Referer', self._referer_url),
                   ('User-Agent', self._useragent)]
        if not header is None  :
            headers.append(header)

        if compress:
            headers.append(('Accept-encoding', 'gzip'))
        opener= None

        if proxy_url is not None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {"http":"http://%s:%s" % (proxy_url, proxy_port),
                       "https":"https://%s:%s" % (proxy_url, proxy_port)}
            proxy_support = urllib2.ProxyHandler(proxies)
            handlers.append(proxy_support)
        if handler is not None:
            handlers.append(handler)
        if cookiejar is not None:
            handlers.append(urllib2.HTTPCookieProcessor(cookiejar))
        handlers.append(AGOLRedirectHandler())
        if len(handlers) > 0:
            opener = urllib2.build_opener(*handlers)
        opener.addheaders = headers
        if len(str(urllib.urlencode(param_dict))) + len(url)> 1999:
            resp = opener.open(url, data=urllib.urlencode(param_dict))
        else:
            format_url = url + "?%s" % urllib.urlencode(param_dict)
            resp = opener.open(format_url)
        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            resp_data = f.read()
        else:
            resp_data = resp.read()
        if resp_data == "" or resp_data == None or resp_data == 'null':
            return ""
        result = None
        try:
            result = json.loads(resp_data)
        except Exception,e:
            print e
        if result is None:
            return None

        if 'error' in result:
            if result['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._do_get(url=url,
                                        param_dict=param_dict,
                                        proxy_url=proxy_url,
                                        proxy_port=proxy_port,
                                        compress=compress)
        return self._unicode_convert(result)
    #----------------------------------------------------------------------
    def _do_post_stnd(self,
                      url,
                      param_dict,
                      securityHandler=None,
                      proxy_url=None,
                      proxy_port=None,
                      header={}):
        """ performs the POST operation and returns dictionary result """
        handlers = []
        headers = {'Referer': self._referer_url,
                   'User-Agent': self._useragent,
                   'Accept-Encoding': ''}
        if not header is None  :
            headers.append(header)

        if compress:
            headers.append(('Accept-encoding', 'gzip'))
        opener= None

        if proxy_url is not None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {"http":"http://%s:%s" % (proxy_url, proxy_port),
                       "https":"https://%s:%s" % (proxy_url, proxy_port)}
            proxy_support = urllib2.ProxyHandler(proxies)
            handlers.append(proxy_support)
        if handler is not None:
            handlers.append(handler)
        if cookiejar is not None:
            handlers.append(urllib2.HTTPCookieProcessor(cookiejar))
        handlers.append(AGOLRedirectHandler())
        if len(handlers) > 0:
            opener = urllib2.build_opener(handlers)
        urllib2.install_opener(opener)
        if len(header) > 0 :
            headers = dict(headers.items() + header.items())

        request = urllib2.Request(url, urllib.urlencode(param_dict), headers=headers)
        result = ""
        try:

            result = urllib2.urlopen(request,data=urllib.urlencode(param_dict)).read()
        except urllib2.HTTPError,e:
            return {'error':{'code':e.code}}
        if result =="":
            return ""
        jres = json.loads(result)
        if 'error' in jres:
            if jres['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._do_post(url,
                                         param_dict,
                                         securityhandler=securityHandler,
                                         header=header,
                                         proxy_url=proxy_url,
                                         proxy_port=proxy_port)

        return self._unicode_convert(jres)



########################################################################
class BaseWebOperations_old(object):
    """ base class that holds operations for web requests """

    _referer_url = ""
    _useragent = "ArcREST"
    _proxy_url = None
    _proxy_port = None
    #----------------------------------------------------------------------
    def _do_get(self, url, param_dict,
                header=None, proxy_url=None,
                proxy_port=None,compress=True,
                forceStandardLib=False):
        if allowRequests and forceStandardLib == False:
            return self._do_get_requests(url=url,
                                         param_dict=param_dict,
                                         header=header,
                                         proxy_url=proxy_url,
                                         proxy_port=proxy_port,
                                         compress=compress)
        else:
            return self._do_get_stnd(url=url,
                                     param_dict=param_dict,
                                     header=header,
                                     proxy_url=proxy_url,
                                     proxy_port=proxy_port,
                                     compress=compress)
    #----------------------------------------------------------------------
    def _do_post(self, url, param_dict,
                 proxy_url=None, proxy_port=None,
                 header={},
                 forceStandardLib=False):
        """
        performs the POST operation and returns dictionary result

        Inputs:
           url - web address
           param_dict - dictionary object that carriers the REST parameters
           proxy_url - web address/IP of proxy
           proxy_port - web port of proxy
           header - optional headers
           forceStandardLib - optional boolean that make the calls force to use urllib libraries
             regardless of the precence of requests of not.  The default is false.
        """
        if allowRequests and forceStandardLib == False:
            return self._do_post_requests(url=url,
                                          param_dict=param_dict,
                                          proxy_url=proxy_url,
                                          proxy_port=proxy_port,
                                          header=header)
        else:
            return self._do_post_stnd(url=url,
                                      param_dict=param_dict,
                                      proxy_url=proxy_url,
                                      proxy_port=proxy_port,
                                      header=header)
    #----------------------------------------------------------------------
    def _download_file(self, url, save_path,
                       file_name=None, param_dict=None,
                       proxy_url=None, proxy_port=None,
                       forceStandardLib=False):
        """
        Downloads a file using either the standard urllib library or
        the optional request library for python.
        """
        if allowRequests and forceStandardLib == False:
            return self._download_file_requests(url=url,
                                         save_path=save_path,
                                         file_name=file_name,
                                         param_dict=param_dict,
                                         proxy_url=proxy_url,
                                         proxy_port=proxy_port)
        else:
            return self._download_file_stnd(url=url,
                                         save_path=save_path,
                                         file_name=file_name,
                                         param_dict=param_dict,
                                         proxy_url=proxy_url,
                                         proxy_port=proxy_port)
    #----------------------------------------------------------------------------------
    def _post_multipart(self, host, selector,
                        fields, files,
                        ssl=False,port=80,
                        proxy_url=None,proxy_port=None,
                        forceStandardLib=False):
        """ performs a multi-post to AGOL, Portal, or AGS
            Inputs:
               host - string - root url (no http:// or https://)
                   ex: www.arcgis.com
               selector - string - everything after the host
                   ex: /PWJUSsdoJDp7SgLj/arcgis/rest/services/GridIndexFeatures/FeatureServer/0/1/addAttachment
               fields - dictionary - additional parameters like token and format information
               files - tuple array- tuple with the file name type, filename, full path
               ssl - option to use SSL
               proxy_url - string - url to proxy server
               proxy_port - interger - port value if not on port 80

            Output:
               JSON response as dictionary
            Useage:
               import urlparse
               url = "http://sampleserver3.arcgisonline.com/ArcGIS/rest/services/SanFrancisco/311Incidents/FeatureServer/0/10261291"
               parsed_url = urlparse.urlparse(url)
               params = {"f":"json"}
               print _post_multipart(host=parsed_url.hostname,
                               selector=parsed_url.path,
                               files=files,
                               fields=params
                               )
        """
        if allowRequests and forceStandardLib == False:
            return self._post_multipart_requests(host=host,
                                                 selector=selector,
                                                 fields=fields,
                                                files=files,
                                                ssl=ssl,
                                                port=port,
                                                proxy_url=proxy_url,
                                                proxy_port=proxy_port)
        else:
            return self._post_multipart_stnd(host=host,
                                     selector=selector,
                                     fields=fields,
                                     files=files,
                                     ssl=ssl,
                                     port=port,
                                     proxy_url=proxy_url,
                                     proxy_port=proxy_port)
    #----------------------------------------------------------------------
    def _download_file_requests(self,
                                url,
                                save_path,
                                file_name=None,
                                param_dict=None,
                                proxy_url=None,
                                proxy_port=None):
        """
           downloads a file using requests

           Inputs:
             url - web address to download file
             save_path - folder on disk to save content
             file_name - optional - name of the file + extension
                ex: test.txt
            param_dict - python dictionary of Key/Value pairs.  Contains
             things like token, format, etc..
            proxy_url - optional - IP of proxy server
            proxy_port - optional - port of proxy server if the proxy_url
             is given, and the proxy_port is none, the function assumes the
             proxy_port is 80.

            returns:
               string path to file.
        """
        proxies = None
        if not proxy_url is None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {
                "http": "%s:%s" % (proxy_url, proxy_port),
                "https": "%s:%s" % (proxy_url, proxy_port),
            }
        r = requests.get(url,
                         stream=True,
                         params=param_dict,
                         proxies=proxies)
        if file_name is None:
            file_name = r.headers['Content-Disposition']
        save_file = os.path.join(save_path, file_name)
        with open(save_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                f.flush()
        return save_file
    #----------------------------------------------------------------------
    def _do_post_requests(self, url, param_dict, proxy_url=None, proxy_port=None, header={}):
        """
           Performs the POST operation using the requests library
        """
        proxies = None
        if not proxy_url is None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {
                "http": "%s:%s" % (proxy_url, proxy_port),
                "https": "%s:%s" % (proxy_url, proxy_port),
            }
        headers = {'Referer': self._referer_url,
                   'User-Agent': self._useragent,
                   'Accept-Encoding': ''}
        if len(header) > 0 :
            headers = dict(headers.items() + header.items())
        content = requests.post(url=url,
                                data=param_dict,
                                json=None,
                                proxies=proxies,
                                headers=headers,
                                verify=True).content
        jres = json.loads(content)
        if 'error' in jres:
            if jres['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._do_post_requests( url, param_dict,
                                                   proxy_url, proxy_port,
                                                   header=header)
        return jres
    #----------------------------------------------------------------------
    def _do_get_requests(self, url, param_dict, header=None, proxy_url=None, proxy_port=None,compress=True):
        """performs a GET request using requests library"""
        proxies = None
        if not proxy_url is None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {
                "http": "%s:%s" % (proxy_url, proxy_port),
                "https": "%s:%s" % (proxy_url, proxy_port),
            }
        headers = {
            'Referer': self._referer_url,
            'User-Agent': self._useragent
        }
        if not header is None  and \
           len(header.items()) > 0:
            for k,v in header.iteritem():
                headers[k] = v
        if compress:
            headers['Content-Encoding'] = 'gzip'
        content = requests.get(url=url,
                               params=param_dict,
                               proxies=proxies,
                               headers=headers,
                               verify=True).content
        jres = json.loads(content)
        if 'error' in jres:
            if jres['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._do_get_requests(url,
                                                 param_dict,
                                                 headers,
                                                 proxy_url,
                                                 proxy_port,
                                                 compress)
        return jres
    #----------------------------------------------------------------------
    def _assemble_url(self, host, selector, port=80, ssl=False):
        """creates the url string for the request"""
        if not port is None and \
           port != 80:
            if ssl:
                url = "https://%s:%s%s" % (host, port, selector)
            else:
                url = "http://%s:%s%s" % (host, port, selector)
        else:
            if ssl:
                url = "https://%s%s" % (host, selector)
            else:
                url = "http://%s%s" % (host, selector)
        return url
    #----------------------------------------------------------------------
    def _post_multipart_requests(self,
                                 host,
                                 selector,
                                 fields,
                                 files,
                                 ssl=False,
                                 port=80,
                                 proxy_url=None,
                                 proxy_port=None):
        """ performs a multi-post to AGOL, Portal, or AGS
            Inputs:
               host - string - root url (no http:// or https://)
                   ex: www.arcgis.com
               selector - string - everything after the host
                   ex: /PWJUSsdoJDp7SgLj/arcgis/rest/services/GridIndexFeatures/FeatureServer/0/1/addAttachment
               fields - dictionary - additional parameters like token and format information
               files - tuple array- tuple with the file name type, filename, full path
                 ex: [('file', r"c:\temp\test.txt", "text.txt")]
               ssl - option to use SSL
               proxy_url - string - url to proxy server
               proxy_port - interger - port value if not on port 80

            Output:
               JSON response as dictionary
            Useage:
               import urlparse
               url = "http://sampleserver3.arcgisonline.com/ArcGIS/rest/services/SanFrancisco/311Incidents/FeatureServer/0/10261291"
               parsed_url = urlparse.urlparse(url)
               params = {"f":"json"}
               print _post_multipart(host=parsed_url.hostname,
                               selector=parsed_url.path,
                               files=files,
                               fields=params
                               )
        """
        verify = False
        proxies = None
        headers = {'User-agent': 'ArcREST'}
        postFiles = {}
        url = self._assemble_url(host, selector, port, ssl)
        if proxy_url is not None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {"http":"http://%s:%s" % (proxy_url, proxy_port),
                       "https":"https://%s:%s" % (proxy_url, proxy_port)}
        #files come in as name, full file path, file name
        # ex: [('file', r"c:\temp\test.txt", "text.txt")]
        for f in files:
            postFiles[f[0]] = open(f[1], 'rb').read()
            del f
        del files
        content = requests.post(url=url,
                            data=fields,
                            json=None,
                            proxies=proxies,
                            headers=headers,
                            files=postFiles,
                            verify=verify).content
        jres = json.loads(content)
        if 'error' in jres:
            if jres['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._post_multipart_requests(host,
                                                         selector,
                                                         fields,
                                                         files,
                                                         ssl,
                                                         port,
                                                         proxy_url,
                                                         proxy_port)
        return jres
    #----------------------------------------------------------------------
    def _download_file_stnd(self, url, save_path, file_name=None, param_dict=None,proxy_url=None, proxy_port=None):
        """ downloads a file """
        try:
            #if url.find("http://") > -1:
            #    url = url.replace("http://", "https://")
            if proxy_url is not None:
                if proxy_port is None:
                    proxy_port = 80
                proxies = {"http":"http://%s:%s" % (proxy_url, proxy_port),
                           "https":"https://%s:%s" % (proxy_url, proxy_port)}
                proxy_support = urllib2.ProxyHandler(proxies)
                opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler(debuglevel=0),AGOLRedirectHandler())
                urllib2.install_opener(opener)
            else:
                opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=0),AGOLRedirectHandler())
                urllib2.install_opener(opener)


            if param_dict is not None:
                encoded_args = urllib.urlencode(param_dict)
                url = url + '/?' + encoded_args
            file_data = urllib2.urlopen(url)
            file_data.getcode()
            file_data.geturl()
            if file_name is None:
                url = file_data.geturl()
                a = file_data.info().getheader('Content-Disposition')
                if a is not None:
                    a = a.strip()
                    file_name = re.findall(r'filename=\"(.+?)\"', a)[0]
                else:
                    file_name = os.path.basename(file_data.geturl().split('?')[0])
            if hasattr(file_data, "status") and \
               (int(file_data.status) >= 300 and int(file_data.status) < 400):
                self._download_file(url=file_data.geturl(),
                                    save_path=save_path,
                                    file_name=file_name,
                                    proxy_url=self._proxy_url,
                                    proxy_port=self._proxy_port)
                return save_path + os.sep + file_name
            if (file_data.info().getheader('Content-Length')):
                total_size = int(file_data.info().getheader('Content-Length').strip())
                downloaded = 0
                CHUNK = 4096
                with open(save_path + os.sep + file_name, 'wb') as out_file:
                    while True:
                        chunk = file_data.read(CHUNK)
                        downloaded += len(chunk)
                        if not chunk: break
                        out_file.write(chunk)
            elif file_data.headers.maintype=='image':
                with open(save_path + os.sep + file_name, 'wb') as out_file:
                    buf = file_data.read()
                    out_file.write(buf)
            return save_path + os.sep + file_name
        except urllib2.HTTPError, e:
            print "HTTP Error:",e.code , url
            return False
        except urllib2.URLError, e:
            print "URL Error:",e.reason , url
            return False
    #----------------------------------------------------------------------
    def _do_post_stnd(self, url, param_dict, proxy_url=None, proxy_port=None, header={}):
        """ performs the POST operation and returns dictionary result """
        if proxy_url is not None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {"http":"http://%s:%s" % (proxy_url, proxy_port),
                       "https":"https://%s:%s" % (proxy_url, proxy_port)}
            proxy_support = urllib2.ProxyHandler(proxies)
            opener = urllib2.build_opener(proxy_support, AGOLRedirectHandler())
        else:
            opener = urllib2.build_opener(AGOLRedirectHandler())
        urllib2.install_opener(opener)

        headers = {'Referer': self._referer_url,
                   'User-Agent': self._useragent,
                   'Accept-Encoding': ''}
        if len(header) > 0 :
            headers = dict(headers.items() + header.items())

        request = urllib2.Request(url, urllib.urlencode(param_dict), headers=headers)
        result = ""
        try:

            result = urllib2.urlopen(request,data=urllib.urlencode(param_dict)).read()
        except urllib2.HTTPError,e:
            return {'error':{'code':e.code}}
        #result = urllib2.urlopen(request).read()
        if result =="":
            return ""
        jres = json.loads(result)
        if 'error' in jres:
            if jres['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._do_post( url, param_dict, proxy_url, proxy_port)

        return self._unicode_convert(jres)
    #----------------------------------------------------------------------
    def _do_get_stnd(self, url, param_dict, header=None, proxy_url=None, proxy_port=None,compress=True):
        """ performs a get operation """

        headers = [('Referer', self._referer_url),
                   ('User-Agent', self._useragent)]
        if not header is None  :
            headers.append(header)

        if compress:
            headers.append(('Accept-encoding', 'gzip'))
        opener= None

        if proxy_url is not None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {"http":"http://%s:%s" % (proxy_url, proxy_port),
                       "https":"https://%s:%s" % (proxy_url, proxy_port)}
            proxy_support = urllib2.ProxyHandler(proxies)
            opener = urllib2.build_opener(proxy_support, AGOLRedirectHandler())
        else:
            opener = urllib2.build_opener(AGOLRedirectHandler())
        opener.addheaders = headers
        if len(str(urllib.urlencode(param_dict))) + len(url)> 1999:
            resp = opener.open(url, data=urllib.urlencode(param_dict))

        else:
            format_url = url + "?%s" % urllib.urlencode(param_dict)

            resp = opener.open(format_url)

        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            resp_data = f.read()
        else:
            resp_data = resp.read()
        if resp_data == "" or resp_data == None or resp_data == 'null':
            return ""
        result = None
        try:
            result = json.loads(resp_data)
        except Exception,e:
            print e
        if result is None:
            return None

        if 'error' in result:
            if result['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._do_get(url=url,
                                        param_dict=param_dict,
                                        proxy_url=proxy_url,
                                        proxy_port=proxy_port,
                                        compress=compress)
        return self._unicode_convert(result)
    #----------------------------------------------------------------------
    def _get_content_type(self, filename):
        """ gets the content type of a file """
        mntype = mimetypes.guess_type(filename)[0]
        filename, fileExtension = os.path.splitext(filename)
        if mntype is None and\
            fileExtension.lower() == ".csv":
            mntype = "text/csv"
        elif mntype is None and \
            fileExtension.lower() == ".sd":
            mntype = "File/sd"
        elif mntype is None:
            #mntype = 'application/octet-stream'
            mntype= "File/%s" % fileExtension.replace('.', '')
        return mntype
    #----------------------------------------------------------------------------------
    def _post_multipart_stnd(self, host, selector,
                        fields, files,
                        ssl=False,port=80,
                        proxy_url=None,proxy_port=None):
        """ performs a multi-post to AGOL, Portal, or AGS using standard library
            Inputs:
               host - string - root url (no http:// or https://)
                   ex: www.arcgis.com
               selector - string - everything after the host
                   ex: /PWJUSsdoJDp7SgLj/arcgis/rest/services/GridIndexFeatures/FeatureServer/0/1/addAttachment
               fields - dictionary - additional parameters like token and format information
               files - tuple array- tuple with the file name type, filename, full path
               ssl - option to use SSL
               proxy_url - string - url to proxy server
               proxy_port - interger - port value if not on port 80

            Output:
               JSON response as dictionary
            Useage:
               import urlparse
               url = "http://sampleserver3.arcgisonline.com/ArcGIS/rest/services/SanFrancisco/311Incidents/FeatureServer/0/10261291"
               parsed_url = urlparse.urlparse(url)
               params = {"f":"json"}
               print _post_multipart(host=parsed_url.hostname,
                               selector=parsed_url.path,
                               files=files,
                               fields=params
                               )
        """
        content_type, body = self._encode_multipart_formdata(fields, files)
        url = self._assemble_url(host, selector, port, ssl)
        if proxy_url is not None:
            if proxy_port is None:
                proxy_port = 80
            proxies = {"http":"http://%s:%s" % (proxy_url, proxy_port),
                       "https":"https://%s:%s" % (proxy_url, proxy_port)}
            proxy_support = urllib2.ProxyHandler(proxies)
            opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler(debuglevel=0))
            urllib2.install_opener(opener)
        request = urllib2.Request(url)
        request.add_header('User-agent', 'ArcREST')
        request.add_header('Content-type', content_type)
        request.add_header('Content-length', len(body))
        request.add_data(body)
        result = urllib2.urlopen(request).read()
        if result =="":
            return ""
        jres = json.loads(result)
        if 'error' in jres:
            if jres['error']['message'] == 'Request not made over ssl':
                if url.startswith('http://'):
                    url = url.replace('http://', 'https://')
                    return self._post_multipart(host, selector,
                                                fields, files,
                                                ssl=True,port=port,
                                                proxy_url=proxy_url,
                                                proxy_port=proxy_port)
        return self._unicode_convert(jres)
    #----------------------------------------------------------------------------------
    def _encode_multipart_formdata(self, fields, files):
        boundary = mimetools.choose_boundary()
        buf = StringIO()
        for (key, value) in fields.iteritems():
            buf.write('--%s\r\n' % boundary)
            buf.write('Content-Disposition: form-data; name="%s"' % key)
            buf.write('\r\n\r\n' + self._tostr(value) + '\r\n')
        for (key, filepath, filename) in files:
            if os.path.isfile(filepath):
                buf.write('--%s\r\n' % boundary)
                buf.write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (key, filename))
                buf.write('Content-Type: %s\r\n' % (self._get_content_type3(filename)))
                file = open(filepath, "rb")
                try:
                    buf.write('\r\n' + file.read() + '\r\n')
                finally:
                    file.close()
        buf.write('--' + boundary + '--\r\n\r\n')
        buf = buf.getvalue()
        content_type = 'multipart/form-data; boundary=%s' % boundary
        return content_type, buf

    def _encode_multipart_formdataZip(self, fields, files):
        LIMIT = mimetools.choose_boundary()
        CRLF = '\r\n'
        L = []
        for (key, value) in fields.iteritems():
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            if isinstance(value, bool):
                L.append(json.dumps(value))
            elif isinstance(value, list):
                L.append(str(value))
            else:
                L.append(self._tostr(value))
        for (key, value, filename) in files:
            L.append('--' + LIMIT)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: %s' % self._get_content_type3(filename))
            L.append('')
            L.append(open(value, 'rb').read())

        L.append('--' + LIMIT + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % LIMIT
        return content_type, body

    def _get_content_type3(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    #----------------------------------------------------------------------
    def _tostr(self,obj):
        """ converts a object to list, if object is a list, it creates a
            comma seperated string.
        """
        if not obj:
            return ''
        elif isinstance(obj, list):
            return ', '.join(map(self._tostr, obj))
        elif isinstance(obj, bool):
            return json.dumps(obj)
        return str(obj)
    #----------------------------------------------------------------------
    def _unicode_convert(self, obj):
        """ converts unicode to anscii """
        if isinstance(obj, dict):
            return {self._unicode_convert(key): self._unicode_convert(value) for key, value in obj.iteritems()}
        elif isinstance(obj, list):
            return [self._unicode_convert(element) for element in obj]
        elif isinstance(obj, unicode):
            return obj.encode('utf-8')
        else:
            return obj