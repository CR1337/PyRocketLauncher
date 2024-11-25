const chip_template = /*html*/`
    <fieldset class="container">
    <legend class="container-legend">{{upper_letter}}</legend>

    <fuse
        v-for="(_, number) in number_of_fuses"
        :enabled="enabled && !disable_fuses"
        :ask="ask"
        :state="state"
        :letter="letter"
        :number="number"
        :host="host"
    ></fuse>

    </fieldset>
`;

const chip_component = {
    template: chip_template,
    props: {
        enabled: Boolean,
        ask: Boolean,
        state: Object,
        letter: String,
        host: String
    },
    data() {
        return {
            number_of_fuses: 16
        };
    },
    methods: {},
    computed: {
        upper_letter() {
            return this.letter.toUpperCase();
        },
        disable_fuses() {
            return this.state.is_remote;
        }
    },
    mounted() {
        if (this.state.is_remote) {
            this.number_of_fuses = this.state.config.config.fuse_amounts[0];
        }
    }
};
