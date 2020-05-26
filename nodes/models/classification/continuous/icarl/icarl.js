module.exports = function(RED) {
    function iCaRLNode(config) {

        const utils = require('../../../../../utils/utils');

        var node = this;

        node.topic = 'model';

        node.config = {
            // Corresponding python class
            pynode: 'iCaRL',
            layerSizes: config.layerSizes,
            maxInDataSize: parseInt(config.maxInDataSize),
            keepDataSize: parseInt(config.keepDataSize),
            maxOldNum: parseInt(config.maxOldNum)
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("icarl", iCaRLNode);
}