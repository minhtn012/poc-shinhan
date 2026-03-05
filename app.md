### DEMO SHINHAN AUTO EXTRACTION 

## url: http://10.3.11.150:8000

1. Endpoint matching
``` 
http://10.3.11.150:8000/preprocess_and_match
```
    method: POST
    example: curl -X POST -F "file=@layout9_test.png" http://10.3.11.150:8000/preprocess_and_match
output message: 
```json
{
  "status": "success",
  "output_message": "Form matched successfully",
  "form_id": "layout9.png",
  "metrics": {
    "coverage": 1,
    "covered_cells": 16,
    "entropy": 0.870886557853449
  },
  "bboxes": [
    {
      "box": [
        [
          245.7012481689453,
          230.09678649902344
        ],
        [
          618.45751953125,
          228.2732391357422
        ],
        [
          618.2989501953125,
          255.31114196777344
        ],
        [
          245.7089080810547,
          256.93359375
        ]
      ],
      "crop_path": "/static/outputs/layout9_test/crops/layout9_test_crop_0.jpg"
    },
  ],
  "preprocessed_image": "/static/outputs/layout9_test/layout9_test_processed.jpg",
  "unwarped_image": "/static/outputs/layout9_test/layout9_test_unwarped.jpg",
  "debug_image": "/static/outputs/layout9_test/layout9_test_debug.jpg",
  "basename": "layout9_test"
}
```

2. Endpoint OCR
```
http://10.3.11.150:8000/ocr_extract
```
    method: POST
    input: output message from /preprocess_and_match (json body)
    example: curl -X POST -H "Content-Type: application/json" -d '{"status":"success","form_id":"layout8.png","preprocessed_image":"/static/outputs/layout9_test/layout9_test_processed.jpg","unwarped_image":"/static/outputs/layout9_test/layout9_test_unwarped.jpg","debug_image":"/static/outputs/layout9_test/layout9_test_debug.jpg","basename":"layout9_test","bboxes":[{"box":[[245.7,230.1],[618.5,228.3],[618.3,255.3],[245.7,256.9]],"crop_path":"/static/outputs/layout9_test/crops/layout9_test_crop_0.jpg"}]}' http://10.3.11.150:8000/ocr_extract

output message: 
```json
{
  "status": "success",
  "form_id": "layout9.png",
  "preprocessed_image": "/static/outputs/layout9_test/layout9_test_processed.jpg",
  "unwarped_image": "/static/outputs/layout9_test/layout9_test_unwarped.jpg",
  "metrics": {
    "coverage": 1,
    "covered_cells": 16,
    "entropy": 0.945198180844995
  },
  "bboxes": [
    {
      "box": [
        [
          133.5238037109375,
          133.89576721191406
        ],
        [
          733.302734375,
          133.8876190185547
        ],
        [
          733.2973022460938,
          159.34249877929688
        ],
        [
          133.51589965820312,
          159.33839416503906
        ]
      ],
      "crop_path": "/static/outputs/layout9_test/crops/layout9_test_crop_0.jpg",
      "text": "Nguyễn Văn A"
    },
    {
      "box": [
        [
          218.73060607910156,
          178.79660034179688
        ],
        [
          733.2930908203125,
          178.8081512451172
        ],
        [
          733.2879638671875,
          202.7660369873047
        ],
        [
          218.72349548339844,
          202.74459838867188
        ]
      ],
      "crop_path": "/static/outputs/layout9_test/crops/layout9_test_crop_1.jpg",
      "text": "1234567890"
    },

  ]
}
```