# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "debian/contrib-jessie64"

  config.vm.hostname = "mail.medicustek.test"
  config.vm.network "forwarded_port", guest: 25, host: 2525, host_ip: "127.0.0.1"
  config.vm.network "forwarded_port", guest: 465, host: 4650, host_ip: "127.0.0.1"

  config.vm.synced_folder "test_notifications/", "/var/mail"
  
  config.vm.provider "virtualbox" do |vb|
    vb.gui = false 
    vb.memory = "256"
    vb.cpus = "1"
    vb.name = "notification-service-email"
  end

  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "resources/email-server.yml"
  end
end
