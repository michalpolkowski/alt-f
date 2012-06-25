#!/bin/sh

. common.sh
check_cookie
write_header "Lighttpd Setup"

CONF_LIGHTY=/etc/lighttpd/lighttpd.conf
CONF_LIGHTY2=/etc/lighttpd/modules.conf
CONF_PHP=/etc/php.ini
PHP_EDIR=/usr/lib/php5/extensions
CONF_SSL=/etc/lighttpd/conf.d/ssl.conf
CONF_AUTH=/etc/lighttpd/conf.d/auth.conf

if ! ipkg list_installed | grep -q kernel-modules; then IPV6_DIS="disabled"; fi

if test $(grep ^server.use-ipv6 $CONF_LIGHTY | cut -d" " -f3) = '"enable"'; then
	IPV6_CHK="checked"
fi

sroot=$(sed -n 's|^var.server_root.*=.*"\(.*\)"|\1|p' $CONF_LIGHTY)
port=$(grep ^server.port $CONF_LIGHTY | cut -d" " -f3)
sslport=$(sed -n 's/$SERVER\["socket"\] == ":\(.*\)".*/\1/p' $CONF_SSL)

mktt sroot_tt "Serve files from this folder.<br>
You have to create one, such as /mnt/sda2/WebData"
mktt sport_tt "Server port, generaly 80.<br>
If the Alt-F administrative web server is running on the default 80 port,<br>
you have to use a different port, e.g. 8080 (or change the admin server port)."
mktt ssl_tt "Enable https"
mktt sslport_tt "https port, generaly 443.<br>
If the 'stunnel' package is providing https on the Alt-F adminstrative server<br>
you have to use a different port, e.g. 8443 (or change the admin https server port)."
mktt wdav_tt "Enable a reading and writing http server (WebDAV).<br>
Use \"webdav://$HTTP_HOST:$port/webdav\" or \"webdav://$HTTP_HOST:$sslport/webdav\" for write access.<br>
Some clients might require 'http:' or 'https:' instead of 'webdav:'."
mktt udav_tt "User(s) that can use WebDAV<br>
If "anyuser" is selected, all valid users will share the same writing area.<br>
If "anybody" is selected, even guests can write."
mktt udir_tt "Serve users web pages from them "public_html" home folder."
mktt dlist_tt "Generate a folder listing on folders without an index file."
mktt access_tt "Generate server access loggs"
mktt php_tt "Enable PHP. Due to memory constrains enable only if needed and only the needed modules."

# enable access/error log through syslog?
#accesslog.use-syslog       = "enable" access_log.conf
#server.errorlog-use-syslog = "enable" lighttpd.conf

if grep -q '^include.*access_log.conf' $CONF_LIGHTY; then ACESSLOG_CHK="checked"; fi
if grep -q '^include.*dirlisting.conf' $CONF_LIGHTY; then DIRLST_CHK="checked"; fi
if grep -q '^include.*ssl.conf' $CONF_LIGHTY; then SSL_CHK="checked"; fi
if grep -q '^include.*webdav.conf' $CONF_LIGHTY2; then WDAV_CHK="checked"; fi
if grep -q '^include.*userdir.conf' $CONF_LIGHTY2; then	USERDIR_CHK="checked"; fi
if grep -q '^include.*fastcgi.conf' $CONF_LIGHTY2; then
	PHP_CHK="checked"
	PHP_VIS='style="visibility: visible; display: block"' 
else
	PHP_VIS='style="visibility: hidden; display: none"' 
fi

if ! test -x /usr/bin/php; then
	PHP_DIS="disabled"
else
	php_maxupload=$(grep upload_max_filesize $CONF_PHP | cut -d" " -f3)
	php_opt="<tr><td>&emsp;Max upload file size</td><td><input type=text size=4 name=php_maxupload value=\"$php_maxupload\"></td></tr>"

	cnt=0; php_opt="$php_opt<tr><td>&emsp;PHP extensions:</td></tr>"
	for i in $(ls $PHP_EDIR); do
		if test "$cnt" = "0"; then php_opt="$php_opt<tr><td></td>"; fi
		bi=$(basename $i .so)
		CHK=""; if grep -q "^extension=$i" $CONF_PHP; then CHK="checked"; fi
		php_opt="$php_opt<td>$bi</td><td><input type=checkbox $CHK name=$bi value=yes>&emsp;&emsp;</td>"
		cnt=$((cnt+1))
		if test "$cnt" = "5"; then cnt=0; php_opt="$php_opt</tr>
"; fi
	done
	if test "$cnt" != "0"; then php_opt="$php_opt</tr>"; fi
fi

selu=$(sed -n 's/^[^#]*auth.require.*webdav.*"require" *=> *"\(.*\)".*/\1/p' $CONF_AUTH)

useropt="<option>anybody</option><option>anyuser</option>"
if test -z "$selu"; then
	selu="anybody"
elif test "${selu:0:5}" = "user="; then
	selu=${selu:5}
else
	useropt="<option>anybody</option><option selected>anyuser</option>"
fi

while read ln; do
	user=$(echo $ln | cut -d: -f1)
	if test "$user" = "$selu"; then
		useropt="$useropt <option selected> $user</option>"
	else
		useropt="$useropt <option> $user </option>"
	fi
done < /etc/rsyncd.secrets

cat<<-EOF
	<script type="text/javascript">
		function browse_dir_popup(input_id) {
		    start_dir = document.getElementById(input_id).value;
		    if (start_dir == "")
		    	start_dir="/mnt";
			window.open("browse_dir.cgi?id=" + input_id + "?browse=" + start_dir, "Browse", "scrollbars=yes, width=500, height=500");
			return false;
		}
		function php_toogle(obj) {
			targ = document.getElementById("php_id")
			if (obj.checked == true) {
				targ.style.visibility = "visible";
				targ.style.display = "block"
			} else {
				targ.style.visibility = "hidden";
				targ.style.display = "none"
			}
		}
	</script>
	<form name="lighttpd" action="/cgi-bin/lighttpd_proc.cgi" method="post">
	<table>
	<tr><td>Server root</td><td colspan=3><input type=text style="width:100%;" id=root_id name=sroot value="$sroot" $(ttip sroot_tt)></td>
		<td><input type=button onclick="browse_dir_popup('root_id')" value=Browse></td></tr>
	<tr><td></td><td></td><td>on port</td><td><input type=text size=2 style="width:100%;" name=port value="$port" $(ttip sport_tt)></td></tr>
	<tr><td>Enable IPv6</td><td><input type=checkbox $IPV6_DIS $IPV6_CHK name=ipv6 value=yes></td></tr>
	<tr><td>Enable SSL</td><td><input type=checkbox $SSL_CHK name=ssl value=yes $(ttip ssl_tt)>
		<td>on port</td><td><input type=text size=2 style="width:100%;" name=sslport value="$sslport" $(ttip sslport_tt)></td></tr>
	<tr><td>Enable WebDAV</td><td><input type=checkbox $WDAV_DIS $WDAV_CHK id=wdav_id name=wdav value=yes $(ttip wdav_tt)>
		<td>for user</td><td><select $WDAV_DIS id=user_id name=user style="width:100%;" $(ttip udav_tt)>$useropt</select></td></tr>
	<tr><td>Enable User Pages</td><td><input type=checkbox $USERDIR_CHK name=userdir value=yes $(ttip udir_tt)></td></tr>
	<tr><td>Enable Directory Listing</td><td><input type=checkbox $DIRLST_CHK name=dirlist value=yes $(ttip dlist_tt)></td></tr>
	<tr><td>Enable Access Log</td><td><input type=checkbox $ACESSLOG_CHK name=accesslog value=yes $(ttip access_tt)></td>
		<!--td>to syslog</td><td><input type=checkbox $SYSLOG_CHK name=syslog value=yes></td--></tr>
	<tr><td>Enable PHP</td><td><input type=checkbox $PHP_DIS $PHP_CHK name=php value=yes onclick="php_toogle(this)" $(ttip php_tt)></td></tr>
	</table>
	<div id="php_id" $PHP_VIS><table>$php_opt</table></div>
	<table><tr><td></td></tr>
	<tr><td><input type="submit" value="Submit"></td><td>$(back_button)</td></tr>
	</table></form></body></html>
EOF