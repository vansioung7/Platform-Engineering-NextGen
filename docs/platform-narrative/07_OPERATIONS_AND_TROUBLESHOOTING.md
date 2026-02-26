# 07 - Operations and Troubleshooting

## Common Issues

Template not found (`404`):
- Verify folder name and request `template` value.

Generation failed (`400`):
- Missing template variables in payload context.
- Invalid context type/shape.

Unexpected output:
- Confirm `.j2` vs static file handling.
- Verify cloud template defaults and overrides.

## Reliability Practices

- Use preview before download in automation.
- Add tests for template families and golden outputs.
- Keep template changes backward compatible when possible.

## Recommended Next Enhancements

- Input schema validation per template family.
- Endpoint authentication and rate limiting.
- Audit logging for template usage and cloud selections.
