class asf_checkrootkit {

  cron { 'checkrootkit':
    command => "/usr/sbin/chkrootkit | /bin/egrep -v 'nothing found|suspicious files|travis.yml|build-id|no suspect|not found|not infected|Windigo|xbuild-framework|nothing detected|nothing deleted|not promisc|dhclient' 2>&1",
    user    => 'root',
    hour    => 03,
    minute  => 45,
    require => Package['chkrootkit'],
  }

}
