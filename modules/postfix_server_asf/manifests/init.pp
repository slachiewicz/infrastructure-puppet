class postfix_server_asf {

  if $::hostname != 'hermes-vm' {
    include postfix::server
  }

}


