import Ajv from 'ajv';

/**
 * Initialize JSON schema validation with ajv
 */
const ajv = new Ajv({ allErrors: true, useDefaults: true });

/**
 * Create a validator function for JSON schema in uniform
 *
 * @param schema JSON schema to validate
 */
export function createValidator(
  schema: boolean | object
): (model: object) => void {
  const validator = ajv.compile(schema);
  return (model: object): void => {
    validator(model);
    if (validator.errors && validator.errors.length) {
      throw { details: validator.errors };
    }
  };
}
