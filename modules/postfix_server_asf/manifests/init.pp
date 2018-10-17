class postfix_server_asf {

  if $facts['hostname'] != 'hermes-vm' {
    include postfix::server
  }

}


