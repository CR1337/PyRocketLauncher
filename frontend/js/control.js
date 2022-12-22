const control_template = /*html*/`
<div>
    <button
        class="base-button toggle-button"
        @click="toggle_enabled()"
        :checked="enabled"
        title="Enable/Disable buttons"
    ><i
        :class="['las', 'la-' + ((enabled) ? 'toggle-on' : 'toggle-off')]"
    ></i></button>

    <button
        class="base-button toggle-button"
        @click="toggle_ask()"
        :checked="ask"
        title="Toggle confirmation prompt"
    ><i
        :class="['las', 'la-' + ((ask) ? 'question-circle' : 'exclamation-circle')]"
    ></i></button>

    <button
        class="base-button"
        @click="open_editor()"
        style="float: right;"
        title="Program editor"
    ><i
        class="las la-pen"
    ></i></button>
</div>
`;

const control_component = {
    template: control_template,
    data() {
        return {
            enabled: false,
            ask: true
        };
    },
    methods: {
        toggle_enabled() {
            this.enabled = !this.enabled;
            this.$emit('enabled-changed', this.enabled);
        },

        toggle_ask() {
            this.ask = !this.ask;
            this.$emit('ask-changed', this.ask);
        },

        open_editor() {
            window.open("editor.html", "_blank").focus();
        }
    }
};
