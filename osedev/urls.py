#  Copyright (C) 2017 Lex Berezhny <lex@damoti.com>.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import url, include
from osedev import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^notebook/', include('osedev.apps.notebook.urls')),
    url(r'^onboarding/', include('osedev.apps.onboarding.urls')),
    url(r'', include('osedev.apps.main.urls')),
    url(r'', include('osedev.apps.user.urls')),
]