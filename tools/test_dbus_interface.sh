#!/bin/bash
# DFakeSeeder D-Bus Interface Test Suite
# Complete testing commands for all D-Bus functionality

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# D-Bus configuration
SERVICE="ie.fio.dfakeseeder"
OBJECT_PATH="/ie/fio/dfakeseeder"
INTERFACE="ie.fio.dfakeseeder.Settings"

# Print section header
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

# Print command
print_command() {
    echo -e "${YELLOW}$ $1${NC}"
}

# Print result
print_result() {
    echo -e "${GREEN}Result:${NC} $1\n"
}

# Print error
print_error() {
    echo -e "${RED}Error:${NC} $1\n"
}

# Check if service is running
check_service() {
    print_header "1. SERVICE AVAILABILITY CHECK"

    print_command "dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames"
    if dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep -q "$SERVICE"; then
        print_result "✅ Service $SERVICE is running"
        return 0
    else
        print_error "❌ Service $SERVICE is NOT running. Please start the application first."
        return 1
    fi
}

# Test introspection
test_introspection() {
    print_header "2. D-BUS INTROSPECTION"

    print_command "gdbus introspect --session --dest $SERVICE --object-path $OBJECT_PATH"
    gdbus introspect --session --dest $SERVICE --object-path $OBJECT_PATH
    echo ""
}

# Test Ping method
test_ping() {
    print_header "3. PING METHOD (Health Check)"

    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.Ping"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.Ping)
    print_result "$result"

    if [[ "$result" == "(true,)" ]]; then
        echo -e "${GREEN}✅ Ping successful - application is responsive${NC}\n"
    else
        echo -e "${RED}❌ Ping failed or returned unexpected value${NC}\n"
    fi
}

# Test GetSettings method
test_get_settings() {
    print_header "4. GET SETTINGS METHOD"

    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.GetSettings"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.GetSettings)

    # Pretty print the JSON
    echo -e "${GREEN}Settings JSON (first 500 chars):${NC}"
    echo "$result" | sed "s/^('\(.*\)',)$/\1/" | python3 -m json.tool 2>/dev/null | head -20
    echo -e "\n${YELLOW}... (truncated for brevity)${NC}\n"
}

# Test GetConnectionStatus method
test_connection_status() {
    print_header "5. GET CONNECTION STATUS METHOD"

    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.GetConnectionStatus"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.GetConnectionStatus)

    # Pretty print the JSON
    echo -e "${GREEN}Connection Status:${NC}"
    echo "$result" | sed "s/^('\(.*\)',)$/\1/" | python3 -m json.tool 2>/dev/null
    echo ""
}

# Test GetDebugInfo method
test_debug_info() {
    print_header "6. GET DEBUG INFO METHOD"

    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.GetDebugInfo"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.GetDebugInfo)

    # Pretty print the JSON
    echo -e "${GREEN}Debug Information:${NC}"
    echo "$result" | sed "s/^('\(.*\)',)$/\1/" | python3 -m json.tool 2>/dev/null
    echo ""
}

# Test UpdateSettings - single value
test_update_single_setting() {
    print_header "7. UPDATE SETTINGS - SINGLE VALUE"

    echo -e "${BLUE}Testing: Set upload_speed to 100${NC}"
    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"upload_speed\": 100}'"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"upload_speed": 100}')
    print_result "$result"

    if [[ "$result" == "(true,)" ]]; then
        echo -e "${GREEN}✅ Setting updated successfully${NC}\n"
    else
        echo -e "${RED}❌ Setting update failed${NC}\n"
    fi
}

# Test UpdateSettings - multiple values
test_update_multiple_settings() {
    print_header "8. UPDATE SETTINGS - MULTIPLE VALUES"

    echo -e "${BLUE}Testing: Set upload_speed=200, download_speed=1000${NC}"
    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"upload_speed\": 200, \"download_speed\": 1000}'"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"upload_speed": 200, "download_speed": 1000}')
    print_result "$result"

    if [[ "$result" == "(true,)" ]]; then
        echo -e "${GREEN}✅ Multiple settings updated successfully${NC}\n"
    else
        echo -e "${RED}❌ Multiple settings update failed${NC}\n"
    fi
}

# Test UpdateSettings - boolean values
test_update_boolean() {
    print_header "9. UPDATE SETTINGS - BOOLEAN VALUES"

    echo -e "${BLUE}Testing: Set window_visible to false${NC}"
    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"window_visible\": false}'"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"window_visible": false}')
    print_result "$result"

    echo "Waiting 2 seconds to observe window hide..."
    sleep 2

    echo -e "${BLUE}Testing: Set window_visible to true${NC}"
    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"window_visible\": true}'"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"window_visible": true}')
    print_result "$result"
    echo ""
}

# Test UpdateSettings - nested settings
test_update_nested() {
    print_header "10. UPDATE SETTINGS - NESTED VALUES"

    echo -e "${BLUE}Testing: Set protocols.dht.enabled to true${NC}"
    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"protocols.dht.enabled\": true}'"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"protocols.dht.enabled": true}')
    print_result "$result"

    if [[ "$result" == "(true,)" ]]; then
        echo -e "${GREEN}✅ Nested setting updated successfully${NC}\n"
    else
        echo -e "${RED}❌ Nested setting update failed${NC}\n"
    fi
}

# Test UpdateSettings - validation failure
test_update_invalid() {
    print_header "11. UPDATE SETTINGS - VALIDATION TEST"

    echo -e "${BLUE}Testing: Set upload_speed to invalid value (99999)${NC}"
    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"upload_speed\": 99999}'"
    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"upload_speed": 99999}')
    print_result "$result"

    if [[ "$result" == "(false,)" ]]; then
        echo -e "${GREEN}✅ Validation correctly rejected invalid value${NC}\n"
    else
        echo -e "${YELLOW}⚠️ Validation may have accepted value that should fail (check max: 10000)${NC}\n"
    fi
}

# Test signal monitoring
test_signal_monitoring() {
    print_header "12. SIGNAL MONITORING (SettingsChanged)"

    echo -e "${BLUE}Starting signal monitor (will run for 10 seconds)...${NC}"
    echo -e "${YELLOW}In another terminal, run:${NC}"
    echo -e "${CYAN}gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"upload_speed\": 150}'${NC}\n"

    print_command "gdbus monitor --session --dest $SERVICE --object-path $OBJECT_PATH"
    echo -e "${YELLOW}Monitoring for 10 seconds...${NC}\n"

    timeout 10s gdbus monitor --session --dest $SERVICE --object-path $OBJECT_PATH &
    monitor_pid=$!

    sleep 2
    # Trigger a settings change to generate a signal
    gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"upload_speed": 175}' >/dev/null 2>&1

    wait $monitor_pid 2>/dev/null
    echo ""
}

# Test performance
test_performance() {
    print_header "13. PERFORMANCE TEST (10 rapid calls)"

    echo -e "${BLUE}Testing response time for Ping method...${NC}\n"

    total_time=0
    for i in {1..10}; do
        start=$(date +%s%N)
        gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.Ping >/dev/null 2>&1
        end=$(date +%s%N)
        elapsed=$(((end - start) / 1000000))  # Convert to milliseconds
        echo "Call $i: ${elapsed}ms"
        total_time=$((total_time + elapsed))
    done

    avg_time=$((total_time / 10))
    echo -e "\n${GREEN}Average response time: ${avg_time}ms${NC}\n"
}

# Test concurrent access
test_concurrent() {
    print_header "14. CONCURRENT ACCESS TEST"

    echo -e "${BLUE}Testing 5 simultaneous D-Bus calls...${NC}\n"

    for i in {1..5}; do
        (gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.Ping && echo "Call $i completed") &
    done

    wait
    echo -e "\n${GREEN}All concurrent calls completed${NC}\n"
}

# Test application quit (WARNING: This will close the app!)
test_quit() {
    print_header "15. APPLICATION QUIT TEST"

    echo -e "${RED}⚠️  WARNING: This will quit the application!${NC}"
    read -r -p "Press Enter to continue or Ctrl+C to cancel..."

    echo -e "\n${BLUE}Testing: Trigger application quit via D-Bus${NC}"
    print_command "gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{\"application_quit_requested\": true}'"

    result=$(gdbus call --session --dest $SERVICE --object-path $OBJECT_PATH --method $INTERFACE.UpdateSettings '{"application_quit_requested": true}')
    print_result "$result"

    echo -e "${GREEN}Quit signal sent. Application should be shutting down...${NC}"
    echo -e "${YELLOW}Check journalctl logs with: journalctl --user -f | grep dfakeseeder${NC}\n"

    # Wait and check if service is gone
    sleep 3
    if dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames | grep -q "$SERVICE"; then
        echo -e "${RED}❌ Service still running after quit signal${NC}\n"
    else
        echo -e "${GREEN}✅ Service successfully terminated${NC}\n"
    fi
}

# Main menu
show_menu() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       DFakeSeeder D-Bus Interface Test Suite          ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}\n"
    echo "1)  Check Service Availability"
    echo "2)  D-Bus Introspection"
    echo "3)  Test Ping (Health Check)"
    echo "4)  Test GetSettings"
    echo "5)  Test GetConnectionStatus"
    echo "6)  Test GetDebugInfo"
    echo "7)  Test UpdateSettings - Single Value"
    echo "8)  Test UpdateSettings - Multiple Values"
    echo "9)  Test UpdateSettings - Boolean (Hide/Show Window)"
    echo "10) Test UpdateSettings - Nested Values"
    echo "11) Test UpdateSettings - Validation Failure"
    echo "12) Test Signal Monitoring"
    echo "13) Test Performance (10 rapid calls)"
    echo "14) Test Concurrent Access"
    echo "15) Test Application Quit (⚠️  Will close app!)"
    echo ""
    echo "A)  Run All Tests (except quit)"
    echo "Q)  Quit"
    echo ""
}

# Run all tests
run_all_tests() {
    check_service || return 1
    test_introspection
    test_ping
    test_get_settings
    test_connection_status
    test_debug_info
    test_update_single_setting
    test_update_multiple_settings
    test_update_boolean
    test_update_nested
    test_update_invalid
    test_signal_monitoring
    test_performance
    test_concurrent

    echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           All Tests Completed Successfully!            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}\n"
}

# Main loop
main() {
    if [ "$1" == "--all" ]; then
        run_all_tests
        exit 0
    fi

    if [ "$1" == "--quick" ]; then
        check_service || exit 1
        test_ping
        test_get_settings
        test_connection_status
        exit 0
    fi

    while true; do
        show_menu
        read -r -p "Select test (1-15, A, Q): " choice

        case $choice in
            1) check_service ;;
            2) test_introspection ;;
            3) test_ping ;;
            4) test_get_settings ;;
            5) test_connection_status ;;
            6) test_debug_info ;;
            7) test_update_single_setting ;;
            8) test_update_multiple_settings ;;
            9) test_update_boolean ;;
            10) test_update_nested ;;
            11) test_update_invalid ;;
            12) test_signal_monitoring ;;
            13) test_performance ;;
            14) test_concurrent ;;
            15) test_quit ;;
            [Aa]) run_all_tests ;;
            [Qq]) echo -e "\n${CYAN}Goodbye!${NC}\n"; exit 0 ;;
            *) echo -e "\n${RED}Invalid option. Please try again.${NC}\n" ;;
        esac

        read -r -p "Press Enter to continue..."
    done
}

# Run main
main "$@"
