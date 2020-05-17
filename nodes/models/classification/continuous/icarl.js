module.exports = function(RED) {
    function iCaRLNode(config) {

        const utils = require('../../../../utils/utils');

        var node = this;

        node.topic = 'model';
        // TODO: define that this is a streaming node

        node.config = {
            // Corresponding python function
            pyfunc: 'icarl',
            layerSizes: config.layerSizes,
            maxInDataSize: parseInt(config.maxInDataSize),
            keepDataSize: parseInt(config.keepDataSize),
            maxOldNum: parseInt(config.maxOldNum)
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("icarl", iCaRLNode);
}