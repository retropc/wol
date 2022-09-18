#!/usr/bin/env python3

import web
import config
import subprocess
import urllib.parse
import html
import hmac
import time
import hashlib

urls = (
  "/wake", "Wake",
  "/", "Listing",
)

class Listing:
  def GET(self):
    now = int(time.time() + config.EXPIRY)
    done_mac = web.input().get("done_mac")
    targets = "".join(self.encode(mac, name, mac == done_mac, now) for mac, name in config.MACHINES.items())

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>wakeonlan</title>
</head>
<h1>wakeonlan</h1>
<body>
  <ul>
{targets}
  </ul>
</body>
"""

  def encode(self, mac, name, done, expiry):
    is_done = "DONE" if done else ""
    return f"""
<li>
  <form method="POST" action="/wake">
    <input type="hidden" name="hmac" value="{generate_hmac(expiry, mac)}" />
    <input type="hidden" name="expiry" value="{expiry}" />
    <input type="hidden" name="mac" value="{html.escape(mac)}" />
    <input type="submit" value="{html.escape(name)}" /> {is_done}
  </form>
</li>
"""

class Wake:
  def POST(self):
    i = web.input()

    hmac_expected = generate_hmac(i.expiry, i.mac)
    if not hmac.compare_digest(hmac_expected, i.hmac):
      raise Exception("bad hmac")
    if time.time() > int(i.expiry):
      raise Exception("expired")

    name = config.MACHINES[i.mac]
    subprocess.check_call(config.WAKEONLAN_BINARY + [i.mac])
    web.seeother("/?done_mac=%s" % urllib.parse.quote(i.mac))

def generate_hmac(expiry, mac):
  return hmac.HMAC(config.SECRET, ("%s %s" % (expiry, mac)).encode("utf-8"), digestmod=hashlib.sha256).hexdigest()

if __name__ == "__main__":
  web.config.debug = False
  app = web.application(urls, globals())
  app.run()
else:
  app = web.application(urls, globals())
  wsgiapp = app.wsgifunc()
