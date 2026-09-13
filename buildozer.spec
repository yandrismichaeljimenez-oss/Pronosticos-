[app]
title = Pronosticos Fijas
package.name = pronosticosfijas
package.domain = com.cuba.fijas
source.dir =.
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,requests,urllib3
orientation = portrait
fullscreen = 0
android.permissions = INTERNET

[buildozer]
log_level = 2

[app:build]

[buildozer:android]
android.api = 33
android.minapi = 21
android.ndk = 25b
