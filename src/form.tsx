import * as React from 'react';
import { Dialog, ReactWidget } from '@jupyterlab/apputils';
import { AutoForm } from 'uniforms-material';

export class Form<T> extends Dialog<T> {
  constructor(schema: any) {
    super({
      body: new FormBody(schema)
    });
  }
  /**
   * Resolve the current dialog.
   *
   * @param index - An optional index to the button to resolve.
   *
   * #### Notes
   * Will default to the defaultIndex.
   * Will resolve the current `show()` with the button value.
   * Will be a no-op if the dialog is not shown.
   */
  resolve(index?: number): void {
    // Valid the form
    console.log('call submit');

    // Resolve the dialog
    super.resolve(index);
  }
}

class FormBody<T> extends ReactWidget implements Dialog.IBodyWidget<T> {
  constructor(schema: any) {
    super();
    this._schema = schema;
  }
  render(): JSX.Element {
    return <AutoForm schema={this._schema} onSubmit={console.log} />;
  }

  private _schema: any;
}
