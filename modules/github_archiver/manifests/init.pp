#/etc/puppet/modules/github_archiver/manifests/init.pp

class github_archiver () {

  ## GitHub Archiver CGI and unicode messaging lib
  ## YAML is pulled elsemethod.
  file {
    '/x1/gitbox/cgi-bin/archiver.cgi':
      ensure => present,
      owner  => 'www-data',
      group  => 'www-data',
      mode   => '0755',
      source => 'puppet:///modules/github_archiver/archiver.py';
    '/x1/gitbox/cgi-bin/messaging.py':
      ensure => present,
      owner  => 'www-data',
      group  => 'www-data',
      mode   => '0755',
      source => 'puppet:///modules/github_archiver/messaging.py';

  }

}
