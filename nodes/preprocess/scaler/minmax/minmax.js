module.exports = function(RED) {
    function MinMaxScalerNode(config) {

        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'data';

        node.config = {
            // Corresponding python class
            pynode: 'MinMaxScaler'
        };

        utils.run(RED, node, config);
    }
    RED.nodes.registerType('minmax scaler', MinMaxScalerNode);
}