[app]
title = Pronosticos Fijas
package.name = pronosticosfijas
package.domain = com.yandris.pronosticos
source.dir =.
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy
orientation = portrait

[buildozer]
log_level = 2

[app:android]
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license_agreement = True
