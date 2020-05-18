import { Dialog, ReactWidget } from '@jupyterlab/apputils';
import { ThemeProvider } from '@material-ui/core/styles';
import { JSONObject, PromiseDelegate } from '@phosphor/coreutils';
import * as React from 'react';
import { AutoForm, AutoFields, ErrorsField } from 'uniforms-material';
import { Form } from './tokens';
import { getMuiTheme } from './theme';
import { Bridge } from 'uniforms';

/**
 * Show a form
 *
 * @param options Form options
 */
export async function showForm(
  options: Form.IOptions
): Promise<Dialog.IResult<JSONObject>> {
  return new FormDialog(options).launch();
}

/**
 * Form within a JupyterLab dialog
 */
class FormDialog extends Dialog<JSONObject> {
  /**
   * Form constructor
   *
   * @param options Form options
   */
  constructor(options: Form.IOptions) {
    super({
      ...options,
      body: new FormWidget(options.schema),
      buttons: [
        Dialog.cancelButton({ label: options.cancelLabel }),
        Dialog.okButton({ label: options.okLabel })
      ]
    });

    this.addClass('jpproject-Form');
  }

  /**
   * Handle the DOM events for the directory listing.
   *
   * @param event - The DOM event sent to the widget.
   *
   * #### Notes
   * This method implements the DOM `EventListener` interface and is
   * called in response to events on the panel's DOM node. It should
   * not be called directly by user code.
   */
  handleEvent(event: Event): void {
    switch (event.type) {
      case 'focus':
        // Prevent recursion error with Material-UI combobox
        event.stopImmediatePropagation();
        break;
      default:
        break;
    }
    super.handleEvent(event);
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

      // this._body is private... Dialog API is bad for inheritance
      // eslint-disable-next-line @typescript-eslint/ban-ts-ignore
      // @ts-ignore
      this._body
        .submit()
        .then(() => {
          super.resolve(index);
        })
        .catch((reason: any) => {
          console.log(`Invalid form field:\n${reason}`);
        });
    }
  }
}

/**
 * Widget containing a form automatically constructed from
 * a uniform.Bridge
 */
class FormWidget extends ReactWidget implements Form.IWidget {
  /**
   * Form widget constructor
   *
   * @param schema Schema defining the form
   */
  constructor(schema: Bridge) {
    super();
    this._schema = schema;
  }

  /**
   * Get the form value
   */
  getValue(): JSONObject | null {
    return this._model;
  }

  /**
   * Render the form
   */
  render(): JSX.Element {
    const theme = getMuiTheme();

    return (
      <ThemeProvider theme={theme}>
        <AutoForm
          className={'jp-project-form'}
          ref={(ref: typeof AutoForm): void => {
            this._formRef = ref;
          }}
          schema={this._schema}
          onSubmit={(model: JSONObject): void => {
            this._model = model;
          }}
        >
          <div className={'jp-project-form-fields'}>
            <AutoFields />
          </div>
          <ErrorsField className={'jp-project-form-errors'} />
        </AutoForm>
      </ThemeProvider>
    );
  }

  /**
   * Submit the form
   *
   * The promise is resolved if the form is valid otherwise it is rejected.
   */
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
  private _schema: Bridge;
}
