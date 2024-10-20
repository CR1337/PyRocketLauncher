const chip_template = /*html*/`
    <fieldset class="container">
    <legend class="container-legend">{{upper_letter}}</legend>

    <fuse
        v-for="(_, number) in number_of_fuses"
        :enabled="enabled"
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
        }
    }
};
