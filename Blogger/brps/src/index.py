# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
# Copyright (C) 2008  Yu-Jie Lin
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import simplejson as json
import StringIO
import logging
import os

from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError 

from brps import post


def send_json(response, obj, callback):
  json_result = obj
  if not isinstance(obj, (str, unicode)):
    json_result = json.dumps(obj)

  response.headers['Content-Type'] = 'application/json'
  if callback:
    response.out.write('%s(%s)' % (callback, json_result))
  else:
    response.out.write(json_result)


def json_error(response, code, msg, callback):
  # 1 - Missing Ids
  # 2 - GAE problem
  # 3 - Server is processing, try again
  # 99 - Unknown problem
  # TODO sends 500
  send_json(response, {'code': code, 'error': msg}, callback)


class HomePage(webapp.RequestHandler):

  def get(self):
    template_values = {}
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))


class GetPage(webapp.RequestHandler):
  """Serves relates posts"""

  def get(self):
    callback = self.request.get('callback')
    try:
      blog_id = int(self.request.get('blog'))
      post_id = int(self.request.get('post'))
    except ValueError:
      json_error(self.response, 1, 'Missing Ids', callback)
      return

    try:
      p = post.get(blog_id, post_id)
      if not p:
        try:
          p = post.add(blog_id, post_id)
        except CapabilityDisabledError:
          logging.debug('Caught CapabilityDisabledError')
          json_error(self.response, 2, 'Unable to process, Google App Engine may be under maintenance.', callback)
          return
      if p:
        send_json(self.response, p.relates, callback)
      else:
        json_error(self.response, 99, 'Unable to get related posts', callback)
    except DownloadError:
      # Should be a timeout, just tell client to retry in a few seconds
      json_error(self.response, 3, 'BRPS server is processing for this post... will retry in a few seconds...', callback)


application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/get', GetPage),
     ],
    debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
