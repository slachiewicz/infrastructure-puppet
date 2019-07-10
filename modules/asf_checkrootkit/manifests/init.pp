class asf_checkrootkit {

  cron { 'checkrootkit':
    command => '/usr/sbin/chkrootkit 2>&1',
    user    => 'root',
    hour    => 20,
    minute  => 45,
    require => Package['chkrootkit'],
  }

}
