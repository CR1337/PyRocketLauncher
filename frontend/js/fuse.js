const fuse_template = /*html*/`
    <fieldset class="container" style="display: inline;">
    <legend class="container-legend">{{number}}</legend>

    <table>
        <tr>
            <span :class="['tooltip', 'icon', status_icon_color]">
                <i :class="['las', status_icon_id]"></i>
                <span v-if="faulty" class="tooltiptext">{{faulty_reason}}</span>
            </span>
        </tr>
        <tr>
            <progress
                min="0"
                :max="timestamp"
                :value="seconds_left"
                :content="progress_string"
                v-if="program_loaded"
            ><span class="tooltiptext">{{name}}</span></progress>

            <button
                :class="['base-button', 'yellow', button_status.fire]"
                @click="fire_button_clicked"
                :disabled="!enabled"
                title="Fire"
                v-else
            ><i
                class="las la-fire-alt"
            ></i></button>
        </tr>
    </table>

    </fieldset>
`;

const fuse_component = {
    template: fuse_template,
    props: {
        enabled: Boolean,
        ask: Boolean,
        state: Object,
        letter: String,
        number: Number,
        host: String,
    },
    data() {
        return {
            button_status: {
                fire: ''
            }
        };
    },
    methods: {
        _error_callback() {
            this.error_occured = true;
        },

        fire_button_clicked() {
            button_request(
                this.host + "/fire", 'POST',
                {
                    letter: this.letter,
                    number: this.number
                },
                'fire', "Fire " + this.device_id + ":" + this.letter.toUpperCase() + this.number.toString() + "?",
                this.ask, this.button_status, this._error_callback
            );
        },

        commands() {
            let commands = [];
            const command_list = this.state.program.command_list;
            for (let command of command_list) {
                if (
                    command.address.device_id == this.device_id
                    && command.address.letter == this.letter
                    && command.address.number == this.number
                ) {
                    commands.push(command);
                }
            }
            return commands;
        }
    },
    computed: {
        device_id() {
            return this.state.config.config.device_id;
        },

        program_loaded() {
            return this.state.program !== null;
        },

        program_current_timestamp() {
            if (!this.program_loaded) {
                return -1;
            }
            return this.state.program.current_timestamp;
        },

        command() {
            if (!this.program_loaded) {
                return null;
            }
            let commands = this.commands();
            if (commands.length == 0) {
                return null;
            }
            /*
            Return the first command that is not fired yet.
            If there is no such command, return the last command.
            */
            for (let command of commands) {
                if (!command.fired) {
                    return command;
                }
            }
            return commands[commands.length - 1];
        },

        timestamp() {
            if (this.command === null) {
                return -1;
            }
            return this.command.timestamp;
        },

        seconds_left() {
            if (this.command === null) {
                return -1;
            }
            return Math.max(0, this.command.timestamp - this.program_current_timestamp);
        },

        name() {
            if (this.command === null) {
                return "";
            }
            return this.command.name;
        },

        fired() {
            if (this.command === null) {
                return false;
            }
            return this.command.fired;
        },

        fireing() {
            if (this.command === null) {
                return false;
            }
            return this.command.fireing;
        },

        faulty() {
            if (this.command === null) {
                return false;
            }
            return this.command.faulty;
        },

        faulty_reason() {
            if (this.command === null) {
                return "";
            }
            return this.command.faulty_reason;
        },

        status() {
            if (this.command === null) {
                if (this.program_loaded) {
                    return 'unused';
                }
                return 'ready';
            }
            if (this.faulty) {
                return 'faulty';
            }
            if (this.fireing) {
                return 'fireing';
            }
            if (this.fired) {
                return 'fired';
            }
            return 'staged';
        },

        status_icon_color() {
            switch (this.status) {
                case 'unused': return 'gray';
                case 'ready': return 'green';
                case 'faulty': return 'red';
                case 'fireing': return 'yellow';
                case 'fired': return 'gray';
                case 'staged': return 'purple';
            }
        },

        status_icon_id() {
            switch (this.status) {
                case 'unused': return 'la-times-circle';
                case 'ready': return 'la-check-circle';
                case 'faulty': return 'la-exclamation-triangle';
                case 'fireing': return 'la-fire-alt';
                case 'fired': return 'la-fire-alt';
                case 'staged': return 'la-calendar-check';
            }
        },

        progress_string() {
            if (this.seconds_left == -1) {
                return "-";
            } else {
                return Math.round(this.seconds_left).toString();
            }
        }
    }
};
