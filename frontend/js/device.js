const device_template = /*html*/`
    <fieldset class="container">
    <legend class="container-legend" id="device-container-legend">
        <a v-if="on_master_page" :href="host" target="_blank">{{device_id}}</a>
        <template v-else>{{device_id}}</template>
    </legend>
        <div>
            <span :class="['icon', display_system_time_color_class]"><i class="las la-clock"></i></span><span :class="['label', display_system_time_color_class]">{{displayed_system_time}}</span>

            <button
                class="base-button red"
                @click="error_button_clicked"
                v-if="error_occured"
                style="float: right;"
                title="An error occured"
            ><i
                class="las la-exclamation-triangle"
            ></i></button>
            <button
                class="base-button"
                @click="config_button_clicked"
                style="float: right;"
                title="Configuration"
            ><i
                class="las la-wrench"
            ></i></button>
            <button
                class="base-button"
                @click="logs_button_clicked"
                style="float: right;"
                title="Logs"
            ><i
                class="las la-list"
            ></i></button>

            <template v-if="on_master_page && status.version < master_version">
                <button
                    :class="['base-button', 'yellow', button_status.update]"
                    @click="update_button_clicked"
                    style="float: right;"
                    title="Install updates"
                ><i
                    class="las la-sync"
                ></i></button>
            </template>

            <template v-if="on_master_page">
                <button
                    class="base-button"
                    @click="move_up"
                    :disabled="first_in_list"
                    style="float: right;"
                    title="Move device up"
                ><i
                    class="las la-arrow-up"
                ></i></button>
                <button
                    class="base-button"
                    @click="move_down"
                    :disabled="last_in_list"
                    style="float: right;"
                    title="Move device down"
                ><i
                    class="las la-arrow-down"
                ></i></button>
            </template>
        </div>

        <div class="v-spacing"></div>

        <div>
            <button
                :class="['base-button', 'red', button_status.shutdown]"
                @click="shutdown_button_clicked"
                :disabled="!enabled"
                title="Shutdown"
            ><i
                class="las la-power-off"
            ></i></button>

            <button
                :class="['base-button', 'yellow', button_status.reboot]"
                @click="reboot_button_clicked"
                :disabled="!enabled"
                title="Reboot"
            ><i
                class="las la-redo-alt"
            ></i></button>
            <span class="h-spacing"></span>

            <template v-if="on_master_page">
                <button
                    :class="['base-button', 'red', deregister_button_status]"
                    @click="deregister_button_clicked"
                    :disabled="!enabled"
                    title="Deregister"
                ><i
                    class="las la-times"
                ></i></button>
                <span class="h-spacing"></span>
            </template>

            <button
                :class="['base-button', 'yellow', button_status.testloop]"
                @click="testloop_button_clicked"
                :disabled="!testloop_button_enabled"
                title="Testloop"
            ><i
                class="las la-flask"
            ></i></button>
            <span class="h-spacing"></span>
            <button
                :class="['base-button', 'green', button_status.unlock]"
                @click="unlock_button_clicked"
                :disabled="!unlock_button_enabled"
                title="Unlock"
            ><i
                class="las la-lock-open"
            ></i></button>
            <button
                :class="['base-button', 'red', button_status.lock]"
                @click="lock_button_clicked"
                :disabled="!lock_button_enabled"
                title="Lock"
            ><i
                class="las la-lock"
            ></i></button>
            <span class="h-spacing"></span>
            <span :class="['icon', lock_icon_color]"><i :class="['las', lock_icon_id]"></i></span>
            <span class="h-spacing"></span>
            <span :class="['icon', status_icon_color]"><i :class="['las', status_icon_id]"></i></span>
            <span class="label">{{status_text}}</span>
        </div>

        <div v-for="letter in letters">
            <chip
                :enabled="enabled && !is_locked"
                :ask="ask"
                :state="state"
                :letter="letter"
                :host="host"
            ></chip>
        </div>
    </fieldset>
`;

const device_component = {
    template: device_template,
    props: {
        enabled: Boolean,
        ask: Boolean,
        initial_ip_address: String,
        on_master_page: Boolean,
        master_version: Number,
        first_in_list: Boolean,
        last_in_list: Boolean
    },
    data() {
        return {
            ip_address: "",
            error_occured: false,
            state: null,
            event_source: null,
            event_stream_pending_seconds: 0,
            event_stream_timeout_id: null,
            deregister_button_status: '',
            button_status: {
                testloop: '',
                unlock: '',
                lock: '',
                shutdown: '',
                reboot: '',
                update: ''
            }
        };
    },
    methods: {
        _error_callback() {
            this.error_occured = true;
        },

        shutdown_button_clicked(event) {
            const confirm_prompt = "Shutdown device?";
            if (!this.ask) {
                if (!confirm(confirm_prompt)) return;
            }
            button_request(
                this.host + "/shutdown", 'POST',
                {},
                'shutdown', confirm_prompt, this.ask, this.button_status, this._error_callback
            );
        },

        reboot_button_clicked(event) {
            const confirm_prompt = "Reboot device?";
            if (!this.ask) {
                if (!confirm(confirm_prompt)) return;
            }
            button_request(
                this.host + "/reboot", 'POST',
                {},
                'shutdown', confirm_prompt, this.ask, this.button_status, this._error_callback
            );
        },

        deregister_button_clicked(event) {
            this.$emit('deregister-button-clicked', this.device_id);
        },

        testloop_button_clicked(event) {
            button_request(
                this.host + "/testloop", 'POST',
                {},
                'testloop', "Run testloop?", this.ask, this.button_status, this._error_callback
            );
        },

        unlock_button_clicked(event) {
            button_request(
                this.host + "/lock", 'POST',
                {is_locked: false},
                'unlock', "Unlock hardware?", this.ask, this.button_status, this._error_callback
            );
        },

        lock_button_clicked(event) {
            button_request(
                this.host + "/lock", 'POST',
                {is_locked: true},
                'lock', "Lock hardware?", this.ask, this.button_status, this._error_callback
            );
        },

        error_button_clicked(event) {
            this.error_occured = false;
        },

        logs_button_clicked(event) {
            window.open(this.host + "/static/logs.html", "_blank").focus();
        },

        config_button_clicked(event) {
            window.open(this.host + "/static/config.html", "_blank").focus();
        },

        move_up() {
            this.$emit('move-up', this.device_id);
        },

        move_down() {
            this.$emit('move-down', this.device_id);
        },

        update_button_clicked() {
            const confirm_prompt = "Install updates?";
            if (!this.ask) {
                if (!confirm(confirm_prompt)) return;
            }
            button_request(
                this.host + "/update", 'POST',
                {},
                'shutdown', confirm_prompt, this.ask, this.button_status, this._error_callback
            );
        }
    },
    computed: {
        controller_state() {
            if (this.state == null) return 'initializing';
            return this.state.controller.state;
        },

        system_time() {
            if (this.state == null) return "0000-00-00T00:00:00.000";
            return this.state.controller.system_time;
        },

        device_id() {
            if (this.state == null) return "";
            const device_id = this.state.config.config.device_id;
            if (!this.on_master_page) {
                document.title = device_id;
            }
            return device_id;
        },

        chip_amount() {
            if (this.state == null) return 0;
            return this.state.config.config.chip_amount;
        },

        letters() {
            result = [];
            const ascii_letters = "abcdefghijklmnopqrstuvwxyz";
            return ascii_letters.slice(0, this.chip_amount).split('');
        },

        host() {
            return (this.on_master_page)
                ? "http://" + this.ip_address + ":5000"
                : "";
        },

        is_locked() {
            if (this.state == null) return true;
            return this.state.hardware.is_locked;
        },

        program_loaded() {
            if (this.state == null) return false;
            return this.state.program !== null;
        },

        program_scheduled() {
            if (this.state == null) return false;
            return this.state.schedule !== null;
        },

        loaded_program_name() {
            if (!this.program_loaded) {
                return "";
            }
            return this.state.program.name;
        },

        scheduled_program_time() {
            if (!this.state.program_scheduled) {
                return "";
            }
            return this.state.schedule.schduled_time;
        },

        testloop_button_enabled() {
            if (this.state == null) return false;
            if (this.state.controller.state == 'not_loaded') {
                return this.enabled;
            }
            return false;
        },

        unlock_button_enabled() {
            return this.enabled && this.is_locked;
        },

        lock_button_enabled() {
            return this.enabled && !this.is_locked;
        },

        lock_icon_id() {
            return (this.is_locked) ? "la-lock" : "la-lock-open";
        },

        lock_icon_color() {
            return (this.is_locked) ? "red" : "green";
        },

        status_icon_id() {
            switch (this.controller_state) {
                case 'initializing': return 'la-hourglass-half';
                case 'not_loaded': return 'la-expand';
                case 'loaded': return 'la-list-ol';
                case 'scheduled': return 'la-calendar-check';
                case 'running': return 'la-play';
                case 'paused': return 'la-pause-circle';
            }
        },

        status_icon_color() {
            switch (this.controller_state) {
                case 'initializing': return 'yellow';
                case 'not_loaded': return 'gray';
                case 'loaded': return 'green';
                case 'scheduled': return 'purple';
                case 'running': return 'green';
                case 'paused': return 'yellow';
            }
        },

        status_text() {
            switch (this.controller_state) {
                case 'loaded':
                case 'running':
                case 'paused':
                    return this.state.program.name;
                case 'scheduled':
                    return this.state.program.name +  " > " + this.state.schedule.schduled_time.replace("T", " ").split(".")[0];
                default:
                    return "";
            }
        },

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
        this.ip_address = this.initial_ip_address;
        this.event_source = new EventSource(this.host + "/event-stream");
        this.event_source.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.state = data;
            const device_id = this.device_id;
            this.$emit('state-updated', {
                "device_id": device_id,
                "state": data
            });
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
