module.exports = function(RED) {
    function TestModelNode(config) {

        const path = require('path');
        const utils = require('../../utils/utils');

        var node = this;

        node.topic = 'test';
        // Does node have error output
        // node.haserror = true;

        node.config = {
            // Corresponding python function
            pyfunc: 'test',
            end: true,
            metric: config.metric
        };

        utils.run(RED, node, config);

    }
    RED.nodes.registerType("test model", TestModelNode);
}