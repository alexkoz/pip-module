# sqs_workflow module

Before run an application do:
```bash
bash aids/environment.sh
```

To run tests

```bash
python -m unittest discover -s /Users/your-user/projects/sqs_workflow/sqs_workflow/tests -p 'test_*.py
```

## Environment variables:

```S3_BUCKET```  – Name of your S3 bucket. S3://your-bucket-name/

```ACCESS``` – AWS access key

```SECRET``` – AWS secret key

```REGION_NAME``` – AWS region name

```AWS_PROFILE``` – AWS profile

```QUEUE_LINK``` – SQS Queue URL

```SIMILARITY_SCRIPT``` – Path to 1st dummy script. aids/dummy_similarity.py

```SIMILARITY_EXECUTABLE``` – Path to executing module for 1st dummy script

```ROOM_BOX_SCRIPT``` – Path to 2nd dummy script. aids/dummy_roombox.py

```ROOM_BOX_EXECUTABLE```  – Path to executing module for 2nd dummy script

```R_MATRIX_SCRIPT``` – Path to 3rd dummy script. aids/dummy_rmatrix.py

```R_MATRIX_EXECUTABLE``` – Path to executing module for 3rd dummy script

```DOOR_DETECTION_SCRIPT``` – Path to 4th dummy script. aids/dummy_dd.py

```DOOR_DETECTION_EXECUTABLE``` – Path to executing module for 4th dummy script

```INPUT_DIRECTORY``` – Path to input directory for the prepare-for-processing method

```OUTPUT_DIRECTORY``` – Path to output directory for the prepare-for-processing method

```SLACK_URL``` – Your Slack App Incoming Webhook URL

```SLACK_ID``` – Slack personal ID if you want to use a mention

If you want connect email notifications:

```GMAIL_USER``` – Your Gmail login. your-login@example.com (Allow insecure app to access your account)

```GMAIL_PASSW``` – Password from your Gmail account

```GMAIL_TO``` – Receiver email address

## Types of messages

### Preprocessing
Messages which contains ```documentPath``` to JSON file with tour information, names of ```steps``` for which preprocessing will be going.

Request message example:
```json
{
    "messageType": "PREPROCESSING",
    "orderId": "5da5d5164cedfd0050363a2e",
    "inferenceId": 1111,
    "tourId": "1342386",
    "documentPath": "https://path-to-panorama-json",
    "steps": ["ROOM_BOX", "DOOR_DETECTION"]
}
```

### Similarity
Contains information about tour – panoramas, layout information.

Input message example before processing:
```json
{
    "messageType": "SIMILARITY",
    "panoUrl": "https://path-to-pano.JPG",
    "tourId": "5fa1df49014bf357cf250d52",   
    "panoId": "5fa1df55014bf357cf250d64"
}
```

Output message example after processing:
```json
{
  "tourId": "1342240",
  "tourLink": "https://link-to-the-tour",
  "floor": 2,
  "fpUrl": "https://path-to-floor-plan.JPG",
  "panos": [
    {
      "fileUrl": "https://path-to-panorama.JPG",
      "panoId": "5f0f323b5e8a061aff256408",
      "name": "Master Bathroom",
      "createdDate": "15.07.2020 19:43:39",
      "pitch": -1.12,
      "roll": -1.29,
      "yaw": 7.87,
      "layout": [
        {
          "id": "door_185",
          "type": "door",
          "room": "wd5qf67fg2.JPG",
          "text": "Door",
          "points": [
            {
              "x": -167.719764139121,
              "y": -14.715253347286422
            },
            {
              "x": -151.52249553174076,
              "y": -13.899205223210682
            },
            {
              "x": -151.52249553174076,
              "y": 34.802072140212175
            },
            {
              "x": -167.71976409404397,
              "y": 36.41544893621932
            }
          ],
          "zOrder": 3,
          "color": 16777215,
          "elementId": "alpha",
          "doorType": 1,
          "doorDirectionRight": true,
          "pathDirection": -1,
          "pathCorner": 1,
          "rotationOffset": 0,
          "positionOffset": 0,
          "computedValues": {
            "width": 61.4299999144657
          }
        }
      ],
      "input_path": "/path-to-input_path",
      "output_path": "/home/path-to-output_path",
      "hotspot_result": [
        {
          "door_id": "door_194",
          "panorama": "8xzll23e78.JPG",
          "visual_probability": 0.7,
          "key_points": [
            [
              [
                1540.820068359375,
                1320.3416748046875
              ],
              [
                18.034748077392578,
                400.08489990234375
              ]
            ],
            [
              [
                1833.3685302734375,
                952.908447265625
              ],
              [
                152.50750732421875,
                187.87974548339844
              ]
            ],
            [
              [
                1838.0255126953125,
                894.2855834960938
              ],
              [
                153.64047241210938,
                168.87429809570312
              ]
            ],
            [
              [
                1864.2867431640625,
                1001.369384765625
              ],
              [
                162.60958862304688,
                204.75576782226562
              ]
            ],
            [
              [
                1917.2623291015625,
                991.0971069335938
              ],
              [
                179.05368041992188,
                199.212890625
              ]
            ]
          ]
        }
      ]
    }
  ],
  "start": "2020-10-08 15:59:17.052359",
  "end": "2020-10-08 16:02:13.584270"
}
```

### Door Detection
Contains information about door points and different bonds meta.

Message example before processing:
```json
{
    "messageType": "DOOR_DETECTING", 
    "inferenceId": "2020-11-19-1", 
    "fileUrl": "https://path-to-pano-image.JPG", 
    "tourId": "0123", 
    "panoId": "0123"
}
```

Message example after processing:

```json
[
  {
    "createdDate": "16.07.2020 02:26:13",
    "fileUrl": "http://domen.com/img1.JPG",
    "layout": [
      {
        "x": 134.97460548852348,
        "y": -81.00949136890486,
        "type": "corner"
      },
      {
        "x": 44.89013987568783,
        "y": 60.57382621349592,
        "type": "corner"
      },
      {
        "x": 44.89014792056024,
        "y": -81.02934636352592,
        "type": "corner"
      },
      {
        "x": 135.09895116736456,
        "y": 60.46545130151028,
        "type": "corner"
      },
      {
        "x": -45.19433210114725,
        "y": -81.00949490730395,
        "type": "corner"
      },
      {
        "x": -135.02197578544292,
        "y": 60.3577862900935,
        "type": "corner"
      },
      {
        "x": -135.0219838079359,
        "y": -80.98968655382886,
        "type": "corner"
      },
      {
        "x": -45.31867775760836,
        "y": 60.46545483988379,
        "type": "corner"
      },
      {
        "color": 16777215,
        "computedValues": {
          "width": 71.97554911272209
        },
        "doorDirectionRight": True,
        "doorType": 1,
        "elementId": "beta",
        "id": "door_108",
        "pathCorner": 1,
        "pathDirection": 1,
        "points": [
          {
            "x": 35.80435909946351,
            "y": -17.074991679581473
          },
          {
            "x": 44.21902962059778,
            "y": -20.455211700643225
          },
          {
            "x": 44.21902962059778,
            "y": 29.503975135145815
          },
          {
            "x": 35.80435923214196,
            "y": 24.985153472533955
          }
        ],
        "positionOffset": 0,
        "room": "54kbn8dnx4.JPG",
        "rotationOffset": 0,
        "text": "Door",
        "type": "door",
        "zOrder": 3
      },
      {
        "color": 16777215,
        "computedValues": {
          "width": 71.97554911272209
        },
        "doorDirectionRight": True,
        "doorType": 1,
        "elementId": "beta",
        "id": "door_110",
        "pathCorner": 1,
        "pathDirection": 1,
        "points": [
          {
            "x": 35.80435909946351,
            "y": -17.074991679581473
          },
          {
            "x": 44.21902962059778,
            "y": -20.455211700643225
          },
          {
            "x": 44.21902962059778,
            "y": 29.503975135145815
          },
          {
            "x": 35.80435923214196,
            "y": 24.985153472533955
          }
        ],
        "positionOffset": 0,
        "room": "54kbn8dnx4.JPG",
        "rotationOffset": 0,
        "text": "Door",
        "type": "door",
        "zOrder": 3
      }
    ]
  }
]
```

### Room Box

Input message example before processing:
```json
{
    "messageType": "ROOM_BOX",
    "inferenceId": "0123", 
    "fileUrl": "https://path-to-pano.JPG",
    "tourId": "5fa1df49014bf357cf250d52",
    "panoId": "5fa1df55014bf357cf250d64"
}
```

Output message example after processing:
```json
[layout:
  [z0:0, z1:0, uv:[
    [0.874929459690343, 0.0499472701727508],
    [0.6246948329880218, 0.836521256741644],
    [0.6246948553348896, 0.04983696464707826],
    [0.8752748643537904, 0.8359191738972793],
    [0.3744601886079243, 0.04994725051497806],
    [0.12493895615154749, 0.8353210349449639],
    [0.12493893386684474, 0.05005729692317301],
    [0.37411478400664344, 0.83591919355491]]]
],
25l187v00b_rotated.JPG:[:],
models.json:[:],
25l187v00b_allpoints.png:[:],
inference:
  [inference_id:7394979587235]
  ```
  
  ### Rotation
  
  ### R Matrix
  Returns rotation matrix – ```pitch, roll, yaw``` format.
  
  Input message example before processing:
  ```json
{
    "messageType": "R_MATRIX",
    "panoUrl": "https://path-to-pano.JPG",
    "tourId": "5fa1df49014bf357cf250d52", 
    "panoId": "5fa1df55014bf357cf250d64"
}
```
  Output message example after processing:
  ```json
[
    [0.9987129910559471, -0.04888576451258531, -0.013510866889431278],
    [0.0489591807476533, 0.998788638594423, 0.0051531600847442875],
    [0.01316830223102185, -0.007323075477102751, 0.9998876283890858]
]
```
