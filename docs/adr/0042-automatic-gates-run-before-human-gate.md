# Automatic gates run before the human gate

The control plane evaluates `file_exists`, `command`, and `workflow_script` gates before the human gate, regardless of YAML declaration order. Human attention is the most expensive gate resource and must not be requested before automated checks pass. A step therefore returns an automatic failure first; only when all automatic gates pass can the human gate block with an approval-pending reason.
