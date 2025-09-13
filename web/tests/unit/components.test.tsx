import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import userEvent from '@testing-library/user-event';

// Mock components for testing
const Button = ({ children, onClick, ...props }: any) => (
  <button onClick={onClick} {...props}>
    {children}
  </button>
);

const Input = ({ label, error, ...props }: any) => (
  <div>
    <label htmlFor={props.id}>{label}</label>
    <input {...props} />
    {error && <span role="alert">{error}</span>}
  </div>
);

const Modal = ({ isOpen, onClose, children }: any) => (
  isOpen ? (
    <div role="dialog" aria-modal="true">
      <button onClick={onClose} aria-label="Close modal">×</button>
      {children}
    </div>
  ) : null
);

// Extend Jest matchers
expect.extend(toHaveNoViolations);

describe('Component Accessibility Tests', () => {
  test('Button should be accessible', async () => {
    const { container } = render(
      <Button onClick={() => {}}>
        Click me
      </Button>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test keyboard navigation
    const button = screen.getByRole('button');
    button.focus();
    expect(button).toHaveFocus();
    
    // Test click
    fireEvent.click(button);
    expect(button).toHaveBeenCalled();
  });

  test('Input should be accessible', async () => {
    const { container } = render(
      <Input
        id="test-input"
        label="Test Label"
        type="text"
        placeholder="Enter text"
      />
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test label association
    const input = screen.getByLabelText('Test Label');
    expect(input).toBeInTheDocument();
    
    // Test user interaction
    await userEvent.type(input, 'test value');
    expect(input).toHaveValue('test value');
  });

  test('Input with error should be accessible', async () => {
    const { container } = render(
      <Input
        id="error-input"
        label="Error Input"
        error="This field is required"
        aria-invalid="true"
      />
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test error message
    const errorMessage = screen.getByRole('alert');
    expect(errorMessage).toHaveTextContent('This field is required');
    
    // Test aria-invalid
    const input = screen.getByLabelText('Error Input');
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  test('Modal should be accessible', async () => {
    const { container, rerender } = render(
      <Modal isOpen={false} onClose={() => {}}>
        <p>Modal content</p>
      </Modal>
    );
    
    // Modal should not be in DOM when closed
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    
    // Open modal
    rerender(
      <Modal isOpen={true} onClose={() => {}}>
        <p>Modal content</p>
      </Modal>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test modal attributes
    const modal = screen.getByRole('dialog');
    expect(modal).toHaveAttribute('aria-modal', 'true');
    
    // Test close button
    const closeButton = screen.getByLabelText('Close modal');
    expect(closeButton).toBeInTheDocument();
    
    // Test focus management
    expect(closeButton).toHaveFocus();
  });

  test('Form should be accessible', async () => {
    const { container } = render(
      <form>
        <Input
          id="username"
          label="Username"
          type="text"
          required
        />
        <Input
          id="password"
          label="Password"
          type="password"
          required
        />
        <Button type="submit">
          Submit
        </Button>
      </form>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test form structure
    const form = screen.getByRole('form');
    expect(form).toBeInTheDocument();
    
    // Test required fields
    const username = screen.getByLabelText('Username');
    const password = screen.getByLabelText('Password');
    
    expect(username).toHaveAttribute('required');
    expect(password).toHaveAttribute('required');
    
    // Test form submission
    const submitButton = screen.getByRole('button', { name: 'Submit' });
    expect(submitButton).toHaveAttribute('type', 'submit');
  });

  test('Data table should be accessible', async () => {
    const { container } = render(
      <table>
        <caption>Call History</caption>
        <thead>
          <tr>
            <th scope="col">Call ID</th>
            <th scope="col">Start Time</th>
            <th scope="col">Duration</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">12345</th>
            <td>2023-01-01 10:00:00</td>
            <td>00:05:30</td>
            <td>Completed</td>
          </tr>
        </tbody>
      </table>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test table structure
    const table = screen.getByRole('table');
    expect(table).toBeInTheDocument();
    
    // Test caption
    const caption = screen.getByText('Call History');
    expect(caption).toBeInTheDocument();
    
    // Test column headers
    const headers = screen.getAllByRole('columnheader');
    expect(headers).toHaveLength(4);
    
    // Test row headers
    const rowHeaders = screen.getAllByRole('rowheader');
    expect(rowHeaders).toHaveLength(1);
  });

  test('Navigation should be accessible', async () => {
    const { container } = render(
      <nav aria-label="Main navigation">
        <ul>
          <li>
            <a href="/dashboard" aria-current="page">
              Dashboard
            </a>
          </li>
          <li>
            <a href="/call-history">
              Call History
            </a>
          </li>
          <li>
            <a href="/config">
              Configuration
            </a>
          </li>
        </ul>
      </nav>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test navigation structure
    const navigation = screen.getByRole('navigation');
    expect(navigation).toHaveAttribute('aria-label', 'Main navigation');
    
    // Test links
    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(3);
    
    // Test current page indicator
    const currentLink = screen.getByRole('link', { name: 'Dashboard' });
    expect(currentLink).toHaveAttribute('aria-current', 'page');
  });

  test('Loading state should be accessible', async () => {
    const { container } = render(
      <div>
        <div role="status" aria-live="polite">
          Loading data...
        </div>
        <div aria-hidden="true">
          <div className="spinner" />
        </div>
      </div>
    );
    
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    
    // Test loading message
    const status = screen.getByRole('status');
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveTextContent('Loading data...');
    
    // Test hidden spinner
    const spinner = screen.getByRole('generic', { hidden: true });
    expect(spinner).toHaveAttribute('aria-hidden', 'true');
  });
});
