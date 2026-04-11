from tplinkrouterc6u import TplinkRouterProvider

# Connect to router
router = TplinkRouterProvider.get_client(
    host="http://192.168.1.1", password="MakhmuD1234"
)

try:
    router.authorize()

    # --- Router status ---
    status = router.get_status()
    print(f"WAN connected : {status.wan_ipv4_addr}")
    print(f"2.4GHz enabled: {status.wifi_2g_enable}")
    print(f"5GHz enabled  : {status.wifi_5g_enable}")
    print(
        f"Clients       : {status.wired_total} wired, {status.wifi_clients_total} wifi"
    )

    # --- Connected devices ---
    print("\nConnected devices:")
    for device in status.devices:
        print(f"  {device.hostname:<20} {device.macaddr}  {device.ipaddr}")

    # --- Turn WiFi on/off ---
    # router.set_wifi(Connection.HOST_2G, True)   # turn 2.4GHz ON
    # router.set_wifi(Connection.HOST_5G, False)  # turn 5GHz OFF

    # --- Reboot ---
    # router.reboot()

finally:
    router.logout()
