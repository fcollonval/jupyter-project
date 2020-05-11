import { Dialog, ReactWidget, InputDialog } from '@jupyterlab/apputils';
import { JSONObject, PromiseDelegate } from '@phosphor/coreutils';
import * as React from 'react';
import { AutoForm, AutoFields, ErrorsField } from 'uniforms-material';
import { Form } from './tokens';

export async function showForm(
  options: Form.IOptions
): Promise<Dialog.IResult<JSONObject>> {
  const { schema, ...dialogOptions } = options;
  const body = new FormWidget(schema);
  return new FormDialog(body, dialogOptions).launch();
}

class FormDialog extends Dialog<JSONObject> {
  constructor(body: Form.IWidget, options: InputDialog.IOptions) {
    super({
      ...options,
      body: body,
      buttons: [
        Dialog.cancelButton({ label: options.cancelLabel }),
        Dialog.okButton({ label: options.okLabel })
      ]
    });

    this.addClass('jpproject-Form');

    // this._body is private... Dialog API is bad for inheritance
    this._formBody = body;
  }

  /**
   * Resolve the current form if it is valid.
   *
   * @param index - An optional index to the button to resolve.
   *
   * #### Notes
   * Will default to the defaultIndex.
   * Will resolve the current `show()` with the button value.
   * Will be a no-op if the dialog is not shown.
   */
  resolve(index?: number): void {
    if (index === 0) {
      // Cancel button clicked
      super.resolve(index);
    } else {
      // index === 1 if ok button is clicked
      // index === undefined if Enter is pressed
      this._formBody
        .submit()
        .then(() => {
          super.resolve(index);
        })
        .catch(reason => {
          console.log(`Invalid form field:\n${reason}`);
        });
    }
  }

  protected _formBody: Form.IWidget;
}

class FormWidget extends ReactWidget implements Form.IWidget {
  constructor(schema: any) {
    super();
    this._schema = schema;
  }

  getValue(): JSONObject | null {
    return this._model;
  }

  render(): JSX.Element {
    return (
      <AutoForm
        ref={(ref: typeof AutoForm): void => {
          this._formRef = ref;
        }}
        schema={this._schema}
        onSubmit={(model: JSONObject): void => {
          this._model = model;
        }}
      >
        <AutoFields />
        <ErrorsField />
      </AutoForm>
    );
  }

  submit(): Promise<void> {
    const submitPromise = new PromiseDelegate<void>();
    this._formRef
      .submit()
      .then(() => {
        submitPromise.resolve();
      })
      .catch(submitPromise.reject);
    return submitPromise.promise;
  }

  protected _formRef: typeof AutoForm;
  private _model: JSONObject | null = null;
  private _schema: any;
}
