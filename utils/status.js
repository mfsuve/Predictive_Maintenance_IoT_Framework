/**
 * I took this code from this repository:
 * https://github.com/GabrieleMaurina/node-red-contrib-machine-learning 
 */

module.exports = {

    Status: function Status() {

        this.fill = (value) => {
            if (value) {
                this._fill = value;
                return this;
            } else
                return this._fill;
        };

        this.shape = (value) => {
            if (value) {
                this._shape = value;
                return this;
            } else
                return this._shape;
        };

        this.text = (value) => {
            if (value) {
                this._text = value;
                return this;
            } else
                return this._text;
        };

        this.get = () => {
            let value = {};
            value.fill = this._fill || 'yellow';
            value.shape = this._shape || 'dot';
            if (this._text)
                value.text = this._text;
            else if (this._fill == 'yellow')
                value.text = 'processing';
            else if (this._fill == 'red')
                value.text = 'error';
            else if (this._fill == 'blue')
                value.text = 'warning';
            else
                value.text = 'done';
            return value;
        };

        this.clear = () => {
            this.fill(undefined).shape(undefined).text(undefined);
            return {};
        };
    }

};