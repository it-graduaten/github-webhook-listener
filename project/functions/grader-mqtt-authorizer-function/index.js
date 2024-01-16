exports.handler = async (event, _, callback) => {
    return ({
        isAuthenticated: true,
        principalId: 'Unauthenticated',
        policyDocuments: [
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "iot:Connect",
                        // Allow the client to pick any client ID.
                        // In a real setup, this should be decided by the server.
                        "Resource": "arn:aws:iot:eu-central-1:947732858245:client/*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": "iot:Subscribe",
                        "Resource": [
                            "arn:aws:iot:eu-central-1:947732858245:client/*",
                            "arn:aws:iot:eu-central-1:947732858245:topicfilter/server"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": "iot:Receive",
                        "Resource": [
                            "arn:aws:iot:eu-central-1:947732858245:client/*",
                            "arn:aws:iot:eu-central-1:947732858245:topic/server"
                        ]
                    }
                ]
            }
        ],
        disconnectAfterInSeconds: 3600,
        refreshAfterInSeconds: 300
    });
};