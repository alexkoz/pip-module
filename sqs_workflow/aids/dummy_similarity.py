import json
import sys

if __name__ == '__main__':
    result_similarity_json = { "tourId": "1342240",
                               "tourLink": "https://app.docusketch.com/admin/tour/5f0f320d5e8a061aff2563eb?accessKey=5f3e&p.device=Desktop&orderId=5f0f36b25e8a061aff256453&dollhousePreview=1",
                               "floor": 2,
                               "fpUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/hedsy4lixc/5f0f320d5e8a061aff2563ec/Tour/map-images/2-floor-zrk4r6065d.jpg",
                               "panos": [
                                   { "fileUrl": "https://docusketch-production-resources.s3.amazonaws.com/items/hedsy4lixc/5f0f320d5e8a061aff2563ec/Tour/original-images/wd5qf67fg2.JPG",
                                     "panoId": "5f0f323b5e8a061aff256408", "name": "Master Bathroom", "createdDate": "15.07.2020 19:43:39", "pitch": -1.12, "roll": -1.29, "yaw": 7.87, "layout": [ { "id": "door_185", "type": "door", "room": "wd5qf67fg2.JPG", "text": "Door", "points": [ { "x": -167.719764139121, "y": -14.715253347286422 }, { "x": -151.52249553174076, "y": -13.899205223210682 }, { "x": -151.52249553174076, "y": 34.802072140212175 }, { "x": -167.71976409404397, "y": 36.41544893621932 } ], "zOrder": 3, "color": 16777215, "elementId": "alpha", "doorType": 1, "doorDirectionRight": True, "pathDirection": -1, "pathCorner": 1, "rotationOffset": 0, "positionOffset": 0, "computedValues": { "width": 61.4299999144657 } }, { "id": "window_186", "type": "window", "room": "wd5qf67fg2.JPG", "text": "Window", "points": [ { "x": -114.91306226091115, "y": -21.618162652652483 }, { "x": -51.77720232584727, "y": -22.240379687105946 }, { "x": -51.77720232584727, "y": 24.19850867831663 }, { "x": -114.91306226091376, "y": 23.533964068226524 } ], "zOrder": 4, "color": 3373751, "elementId": "alpha", "computedValues": { "width": 152.95739286950206 } } ], "input_path": "/opt/tomcat/uploads/7397827243380/", "output_path": "/home/ubuntu/tmp/delete/inference-result/7397827243380", "hotspot_result": [ { "door_id": "door_194", "panorama": "8xzll23e78.JPG", "visual_probability": 0.7, "key_points": [ [ [ 1540.820068359375, 1320.3416748046875 ], [ 18.034748077392578, 400.08489990234375 ] ], [ [ 1833.3685302734375, 952.908447265625 ], [ 152.50750732421875, 187.87974548339844 ] ], [ [ 1838.0255126953125, 894.2855834960938 ], [ 153.64047241210938, 168.87429809570312 ] ], [ [ 1864.2867431640625, 1001.369384765625 ], [ 162.60958862304688, 204.75576782226562 ] ], [ [ 1917.2623291015625, 991.0971069335938 ], [ 179.05368041992188, 199.212890625 ] ] ] } ] } ],
                               "start": "2020-10-08 15:59:17.052359",
                               "end": "2020-10-08 16:02:13.584270"}
    print(json.dumps(result_similarity_json))

sys.exit(0)
