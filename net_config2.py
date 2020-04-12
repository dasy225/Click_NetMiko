#!/usr/bin/env python3

import colorama
from colorama import Fore, Style

from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoTimeoutException, NetMikoAuthenticationException

from paramiko.ssh_exception import SSHException

import click


class Device(object):
    def __init__(self, ip=None, device_type=None, username=None, password=None):
        self.ip = ip
        self.device_type = device_type
        self.username = username
        self.password = password

# open file and send command with file
def open_send(net_connect, config):
    with open(config) as c:
        config_lines = c.read().splitlines()

    config_set = net_connect.send_config_set(config_lines)
    return print(config_set)


# send show command with user"s input
def show_command(net_connect, cmd):
    output = net_connect.send_command(cmd)
    return print(output)


def connect(device):
    try:
        global net_connect
        net_connect = ConnectHandler(**device)
        return True

    except NetMikoTimeoutException:
        print(Fore.RED + "#" * 70)
        print(Fore.RED + " " * 18 + str(device["ip"]) + " is not reachable...")
        print(Fore.RED + "#" * 70)
        print(Style.RESET_ALL)
        return False

    except NetMikoAuthenticationException:
        print(Fore.RED + "#" * 70)
        print(Fore.RED + " " * 18 + "Authentication failure on " + str(device["ip"]))
        print(Fore.RED + "#" * 70)
        print(Style.RESET_ALL)
        return False

    except SSHException:
        print(Fore.RED + "#" * 70)
        print(Fore.RED + " " * 18 + "SSH is not enabled on " + str(device["ip"]))
        print(Fore.RED + "#" * 70)
        print(Style.RESET_ALL)
        return False


@click.group(invoke_without_command=True)
# file for configuration
@click.option("--config", help="Enter the configuration file name here")
# optional: file for device list
@click.option("--device_list", help="Enter the device list file name here")
# optional: user input show command
@click.option("--cmd", help="Enter the show command here")
# optional: user input device_type, default = cisco_ios
@click.option("--device_type", help="Enter the device type here (default = Cisco IOS)", default="cisco_ios")
# user input ip address
@click.option("--ip", help="Enter the device ip address here")
# prompt user for input username
@click.option("--username",help="device username", prompt=True, hide_input=False)
# promtp user for input password
@click.option("--password",help="device password", prompt=True, hide_input=True)
@click.pass_context


def main(ctx, config, device_list, cmd, device_type, ip, username, password):

    global devices
    devices = []

    if ip:
        device = {
            "device_type": device_type,
            "ip": ip,
            "username": username,
            "password": password}

        devices.append(device)

        print(Fore.MAGENTA + "#" * 70)
        print(" " * 18 + " Connecting to Device: " + ip)
        print(Fore.MAGENTA + "#" * 70 + Style.RESET_ALL)

        connect(device)

        if connect(device) is True:
            if config:
                open_send(net_connect, config)

                output = net_connect.send_command("wr")

                print(Fore.CYAN + "#" * 70)
                print(" " * 18 + " Saving on configurations on: " + ip)
                print(Fore.CYAN + "#" * 70 + Style.RESET_ALL)

            if cmd:
                show_command(net_connect, cmd)

    else:
        with open(device_list) as d:
            for ip in d:
                device = {
                    "device_type": "cisco_ios",
                    "ip": ip,
                    "username": username,
                    "password": password}

                devices.append(device)

                print(Fore.MAGENTA + "#" * 70)
                print(" " * 18 + " Connecting to Device: " + ip)
                print(Fore.MAGENTA + "#" * 70+ Style.RESET_ALL)

                connect(device)

                if connect(device) is True:
                    if config:
                        open_send(net_connect, config)

                        output = net_connect.send_command("wr")

                        print(Fore.CYAN + "#" * 70)
                        print(" " * 18 + " Saving on configurations on: " + ip)
                        print(Fore.CYAN + "#" * 70 + Style.RESET_ALL)

                    if cmd:
                        show_command(net_connect, cmd)
    ctx.obj = devices


@main.command("Check_OSPF")
@click.pass_obj
def check_ospf(devices):
    for device in devices:
        output = net_connect.send_command("show run | sec ospf")
        ospf_commands = ["router ospf 1", "net 0.0.0.0 255.255.255.255 area 0"]
        if not "router ospf" in output:
            print("\n")
            print("~" * 70)
            print(" " * 15 + Fore.WHITE + "OSPF is " + Fore.RED + "not" + Fore.WHITE + " enabled on: " + str(device["ip"]) + Style.RESET_ALL)
            print("~" * 70)
            print("\n")
            answer = input("Would you like you enable default OSPF settings <y/n> :")

            if answer == "y":
                output = net_connect.send_config_set(ospf_commands)
                print(output)
                print("\n")
                print("+" * 70)
                print(" " * 20 + Fore.GREEN + "OSPF is now configured!" + Style.RESET_ALL)
                print("+" * 70)
                print("\n")

                output = net_connect.send_command("wr")

                print(Fore.CYAN + "#" * 70)
                print(" " * 18 + " Saving on configurations on: " + str(device["ip"]))
                print(Fore.CYAN + "#" * 70 + Style.RESET_ALL)

            else:
                print("\n")
                print("-" * 70)
                print(" " * 15 + Fore.RED + "No OSPF configurations have been made!" + Style.RESET_ALL)
                print("-" * 70)
                print("\n")
        else:
            print("\n")
            print(Fore.YELLOW + "+" * 70)
            print( " " * 10 + " OSPF is already configured on this device.")
            print("+" * 70)
            print("\n" + Style.RESET_ALL)


@main.command("Check_EIGRP")
@click.pass_obj
def check_eigrp(devices):
    output = net_connect.send_command("show run | sec eigrp")
    eigrp_commands = ["router eigrp 1", "net 0.0.0.0"]

    for device in devices:
        if not "router eigrp" in output:
            print("\n")
            print("~" * 70)
            print(' ' * 15 + Fore.WHITE + "EIGRP is " + Fore.RED + "not " + Fore.WHITE + "enabled on " + str(device["ip"]) + Style.RESET_ALL)
            print("~" * 70)
            print("\n")
            answer = input("Would you like you enable default EIGRP setting: <y/n>")

            if answer == "y":
                output = net_connect.send_config_set(eigrp_commands)
                print(output)
                print("\n")
                print("+" * 70)
                print(' ' * 20 + Fore.GREEN + "EIGRP is now configured!")
                print("+" * 70)
                print("\n")

                output = net_connect.send_command("wr")

                print(Fore.CYAN + "#" * 70)
                print(" " * 18 + " Saving on configurations on: " + str(device["ip"]))
                print(Fore.CYAN + "#" * 70 + Style.RESET_ALL)

            else:
                print("\n")
                print("-" * 70)
                print(' ' * 15 + Fore.YELLOW + "No EIGRP configurations have been made")
                print("-" * 70)
                print("\n" + Style.RESET_ALL)


        else:
            print("\n")
            print(Fore.CYAN + "+" * 70)
            print( " " * 10 + " EIGRP is already configured on device: " + str(device["ip"]))
            print("+" * 70)
            print("\n" + Style.RESET_ALL)


if __name__ == "__main__":
    main()
    print("Task Completed!")
