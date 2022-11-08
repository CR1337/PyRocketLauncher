/* <span class="h-spacing"></span>
            <button
                :class="['base-button', button_status.set_system_time_now]"
                @click="set_system_time_now_button_clicked"
                :disabled="!set_system_time_now_button_enabled"
            ><i
                class="las la-user-clock"
            ></i></button>
            <button
                :class="['base-button', button_status.set_system_time]"
                @click="set_system_time_button_clicked"
                :disabled="!set_system_time_button_enabled"
            ><i
                class="las la-clock"
            ></i></button>
            <input type="time" step="1" v-model="selected_system_time"></input> */

const master_template = /*html*/`
    <fieldset class="container">
    <legend class="container-legend-icon"><i class="las la-broadcast-tower"></i></legend>
        <div>
            <span :class="['icon', display_system_time_color_class]"><i class="las la-clock"></i></span><span :class="['label', display_system_time_color_class]">{{displayed_system_time}}</span>
            <button
                class="base-button red"
                @click="error_button_clicked"
                v-if="error_occured"
                style="float: right;"
            ><i
                class="las la-exclamation-triangle"
            ></i></button>
            <button
                class="base-button"
                @click="config_button_clicked"
                style="float: right;"
            ><i
                class="las la-wrench"
            ></i></button>
            <button
                class="base-button"
                @click="logs_button_clicked"
                style="float: right;"
            ><i
                class="las la-list"
            ></i></button>
        </div>

        <div class="v-spacing"></div>

        <div>
            <button
                :class="['base-button', button_status.search]"
                @click="search_button_clicked"
                :disabled="!enabled"
            ><i
                class="las la-search"
            ></i></button>
            <button
                :class="['base-button', 'red', button_status.deregister_all]"
                @click="deregister_all_button_clicked"
                :disabled="!deregister_all_button_enabled"
            ><i
                class="las la-times"
            ></i></button>
            <span class="h-spacing"></span>
            <button
                :class="['base-button', 'yellow', button_status.testloop]"
                @click="testloop_button_clicked"
                :disabled="!testloop_button_enabled"
            ><i
                class="las la-flask"
            ></i></button>
            <span class="h-spacing"></span>
            <button
                :class="['base-button', 'green', button_status.unlock]"
                @click="unlock_button_clicked"
                :disabled="!unlock_button_enabled"
            ><i
                class="las la-lock-open"
            ></i></button>
            <button
                :class="['base-button', 'red', button_status.lock]"
                @click="lock_button_clicked"
                :disabled="!lock_button_enabled"
            ><i
                class="las la-lock"
            ></i></button>
        </div>

        <div>
            <button
                :class="['base-button', button_status.load]"
                onclick="document.getElementById('program_file_upload_button').click()"
                :disabled="!load_button_enabled"
            ><i
                class="las la-upload"
            ></i></button>
            <input type="file" id="program_file_upload_button" style="display:none" accept=".json" @change="load_button_clicked">
            <button
                :class="['base-button', 'red', button_status.unload]"
                @click="unload_button_clicked"
                :disabled="!unload_button_enabled"
            ><i
                class="las la-trash-alt"
            ></i></button>
            <button
                :class="['base-button', 'green', button_status.play]"
                @click="play_button_clicked"
                :disabled="!play_button_enabled"
            ><i
                class="las la-play"
            ></i></button>
            <button
                :class="['base-button', 'yellow', button_status.pause]"
                @click="pause_button_clicked"
                :disabled="!pause_button_enabled"
            ><i
                class="las la-pause-circle"
            ></i></button>
            <button
                :class="['base-button', 'yellow', button_status.continue]"
                @click="continue_button_clicked"
                :disabled="!continue_button_enabled"
            ><i
                class="las la-play-circle"
            ></i></button>
            <button
                :class="['base-button', 'red', button_status.stop]"
                @click="stop_button_clicked"
                :disabled="!stop_button_enabled"
            ><i
                class="las la-stop"
            ></i></button>
            <span class="h-spacing"></span>
            <button
                :class="['base-button', 'red', button_status.unschedule]"
                @click="unschedule_button_clicked"
                :disabled="!unschedule_button_enabled"
            ><i
                class="las la-calendar-times"
            ></i></button>
            <button
                :class="['base-button', 'purple', button_status.schedule]"
                @click="schedule_button_clicked"
                :disabled="!schedule_button_enabled"
            ><i
                class="las la-calendar-plus"
            ></i></button>
            <input type="time" step="1" v-model="selected_schedule_time">
        </div>

    </fieldset>

    <div v-for="(device, device_id, _) in devices">
        <device
            :enabled="enabled"
            :ask="ask"
            :initial_ip_address="device.ip_address"
            :on_master_page="true"
            :deregister_button_status="button_status['deregister_' + device_id]"
            @state-updated="device_state_updated"
            @deregister-button-clicked="deregister_device"
        ></device>
    </div>
`;

const master_component = {
    template: master_template,
    props: {
        enabled: Boolean,
        ask: Boolean
    },
    data() {
        return {
            error_occured: false,
            system_time: "###T--:--:--.***",
            devices: {},
            event_source: null,
            last_loaded_program_name: "",
            // selected_system_time: formatted_time(new Date(Date.now())),
            selected_schedule_time: "00:00:00",
            event_stream_pending_seconds: 0,
            event_stream_timeout_id: null,
            button_status: {
                search: '',
                deregister_all: '',
                load: '',
                unload: '',
                play: '',
                pause: '',
                continue: '',
                stop: '',
                testloop: '',
                schedule: '',
                unschedule: '',
                unlock: '',
                lock: '',
                set_system_time: '',
                set_system_time_now: '',
            }
        }
    },
    methods: {
        _error_callback() {
            this.error_occured = true;
        },

        search_button_clicked(event) {
            button_request("/search", 'GET', {}, 'search', "Search for devices?", this.ask, this.button_status, this._error_callback)
            .then((data) => {
                if (data !== null) {
                    this.devices = data;
                    for (let device_id in this.devices) {
                        if (("deregister_" + device_id) in this.button_status) {
                            continue;
                        }
                        this.button_status["deregister_" + device_id] = '';
                    }
                }
            });
        },

        deregister_all_button_clicked(event) {
            button_request("/deregister-all", 'POST', {}, 'deregister_all', "Deregister all devices?", this.ask, this.button_status, this._error_callback)
            .then((data) => {
                if (data !== null) {
                    for (let device_id of this.devices) {
                        if (("deregister_" + device_id) in this.button_status) {
                            delete this.button_status["degerister_" + device_id];
                        }
                    }
                    this.devices = {};
                }
            });
        },

        deregister_device(device_id) {
            button_request("/deregister", 'POST', {device_id: device_id}, 'deregister_' + device_id, 'Deregister ' + device_id + "?", this.ask, this.button_status, this._error_callback)
            .then((data) => {
                if (data !== null) {
                    const device_id = data.deregistered_device_id;
                    delete this.devices[device_id];
                    delete this.button_status["deregister_" + device_id];
                }
            });
        },

        load_button_clicked(event) {
            const reader = new FileReader();
            reader.onload = this._on_reader_loaded;
            this.last_loaded_program_name = event.target.files[0].name;
            reader.readAsText(event.target.files[0]);
        },

        _on_reader_loaded(event) {
            let loaded_program = [];
            try {
                loaded_program = JSON.parse(event.target.result);
                console.log(event.target.result);
            } catch (error) {
                console.log(error);
                console.log(loaded_program);
                alert("The loaded Program is ill formed!\nPlease check the file or choose a different one.");
                return;
            }

            button_request(
                "/program", 'POST',
                {
                    name: this.last_loaded_program_name,
                    event_list: loaded_program
                },
                'load', "Upload program?", this.ask, this.button_status, this._error_callback
            );
        },

        unload_button_clicked(event) {
            button_request(
                "/program", 'DELETE',
                {},
                'unload', "Delete program?", this.ask, this.button_status, this._error_callback
            );
        },

        play_button_clicked(event) {
            button_request(
                "/program/control", 'POST',
                {action: 'run'},
                'play', "Run program?", this.ask, this.button_status, this._error_callback
            );
        },

        pause_button_clicked(event) {
            button_request(
                "/program/control", 'POST',
                {action: 'pause'},
                'pause', "Pause program?", this.ask, this.button_status, this._error_callback
            );
        },

        continue_button_clicked(event) {
            button_request(
                "/program/control", 'POST',
                {action: 'continue'},
                'continue', "Continue program?", this.ask, this.button_status, this._error_callback
            );
        },

        stop_button_clicked(event) {
            button_request(
                "/program/control", 'POST',
                {action: 'stop'},
                'stop', "Stop program?", this.ask, this.button_status, this._error_callback
            );
        },

        testloop_button_clicked(event) {
            button_request(
                "/testloop", 'POST',
                {},
                'testloop', "Run testloop?", this.ask, this.button_status, this._error_callback
            );
        },

        schedule_button_clicked(event) {
            const datetime_string = this._next_datetime_ISOstring(this.selected_schedule_time);
            button_request(
                "/program/control", 'POST',
                {
                    action: 'schedule',
                    time: datetime_string
                },
                'schedule', "Schedule program for " + datetime_string + "?", true, this.button_status, this._error_callback
            );
        },

        unschedule_button_clicked(event) {
            button_request(
                "/program/control", 'POST',
                {action: 'unschedule'},
                'unschedule', "Unschedule program?", this.ask, this.button_status, this._error_callback
            );
        },

        unlock_button_clicked(event) {
            button_request(
                "/lock", 'POST',
                {is_locked: false},
                'unlock', "Unlock hardware?", this.ask, this.button_status, this._error_callback
            );
        },

        lock_button_clicked(event) {
            button_request(
                "/lock", 'POST',
                {is_locked: true},
                'lock', "Lock hardware?", this.ask, this.button_status, this._error_callback
            );
        },

        // set_system_time_button_clicked(event) {
        //     const datetime_string = this._next_datetime_ISOstring(this.selected_system_time);
        //     button_request(
        //         "/system-time", 'POST',
        //         {system_time: datetime_string},
        //         'set_system_time', "Set system time to " + datetime_string + "?", true, this.button_status, this._error_callback
        //     );
        // },

        // set_system_time_now_button_clicked(event) {
        //     const system_time = now_ISOstring();
        //     button_request(
        //         "/system-time", 'POST',
        //         {system_time: system_time},
        //         'set_system_time_now', "Set system time to now (" + system_time + ")?", this.ask, this.button_status, this._error_callback
        //     );
        // },

        error_button_clicked(event) {
            this.error_occured = false;
        },

        logs_button_clicked(event) {
            window.open("logs.html", "_blank").focus();
        },

        config_button_clicked(event) {
            window.open("config.html", "_blank").focus();
        },

        _next_datetime_ISOstring(time_string) {
            const splits = now_ISOstring().split('T');
            const date_string_now = splits[0];
            const time_string_now = splits[1].split('.')[0];

            const target_ISOstring = date_string_now + "T" + time_string + ".000";

            if (time_string_now < time_string) {
                return target_ISOstring;
            }

            let target_date = new Date(Date.parse(target_ISOstring + "Z"));
            target_date.setDate(target_date.getDate() + 1);
            return target_date.toISOString().slice(0, -1);
        },

        device_state_updated(data) {
            const device_id = data.device_id;
            const state = data.state;
            this.devices[device_id] = state;
        }
    },
    computed: {
        _devices_found() {
            return Object.keys(this.devices).length > 0;
        },

        deregister_all_button_enabled() {
            return this.enabled && this._devices_found;
        },

        load_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state == 'not_loaded') {
                    return this.enabled;
                }
            }
            return false;
        },

        unload_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state != 'not_loaded') {
                    return this.enabled;
                }
            }
            return false;
        },

        play_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state == 'loaded') {
                    return this.enabled;
                }
            }
            return false;
        },

        pause_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state == 'running') {
                    return this.enabled;
                }
            }
            return false;
        },

        continue_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state == 'paused') {
                    return this.enabled;
                }
            }
            return false;
        },

        stop_button_enabled() {
            for (device_id in this.devices) {
                if (
                    this.devices[device_id].controller.state == 'running'
                    || this.devices[device_id].controller.state == 'paused'
                ) {
                    return this.enabled;
                }
            }
            return false;
        },

        testloop_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state == 'not_loaded') {
                    return this.enabled;
                }
            }
            return false;
        },

        schedule_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state == 'loaded') {
                    return this.enabled;
                }
            }
            return false;
        },

        unschedule_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].controller.state == 'scheduled') {
                    return this.enabled;
                }
            }
            return false;
        },

        unlock_button_enabled() {
            for (device_id in this.devices) {
                if (this.devices[device_id].hardware.is_locked) {
                    return this.enabled;
                }
            }
            return false;
        },

        lock_button_enabled() {
            for (device_id in this.devices) {
                if (!this.devices[device_id].hardware.is_locked) {
                    return this.enabled;
                }
            }
            return false;
        },

        // set_system_time_button_enabled() {
        //     for (device_id in this.devices) {
        //         if (
        //             this.devices[device_id].controller.state != 'not_loaded'
        //             && this.devices[device_id].controller.state != 'loaded'
        //         ) {
        //             return false;
        //         }
        //     }
        //     return this.enabled;
        // },

        // set_system_time_now_button_enabled() {
        //     return this.set_system_time_button_enabled;
        // },

        displayed_system_time() {
            return this.system_time.split("T")[1].split(".")[0];
        },

        display_system_time_color_class() {
            if (this.event_stream_pending_seconds > 5) {
                return "red";
            } else if (this.event_stream_pending_seconds > 1) {
                return "yellow";
            } else {
                return "";
            }
        }
    },
    created() {
        request("/devices", 'GET', {}, this._error_callback, ()=>{})
        .then((devices) => {
            this.devices = devices;
        });
        this.event_source = new EventSource("/event-stream");
        this.event_source.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.system_time = data.controller.system_time;
            this.event_stream_pending_seconds = 0;
        }
        this.event_stream_pending_seconds = 0;
        this.event_stream_timeout_id = setInterval(() => {
            this.event_stream_pending_seconds++;
        }, 1000);
    },
    beforeUnmount() {
        this.event_source.close();
        clearInterval(this.event_stream_timeout_id);
    }
};
