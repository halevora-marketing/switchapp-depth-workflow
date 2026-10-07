# Security policy

Report security issues privately to the repository owner rather than opening a public issue.

Never commit:

- API keys, OAuth tokens, cookies, passwords, or `.env` files
- signed or short-lived CDN URLs
- private Drive, Sheet, or browser-session data
- personal identity-reference images or videos
- unreviewed production analyses or prompts containing personal information

The CLI does not make network requests. FFmpeg, FFprobe, and ONNX model files are local dependencies supplied by the operator.

