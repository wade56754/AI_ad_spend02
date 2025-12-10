/**
 * 示例测试：Button 组件
 *
 * 这是一个完整的测试示例，展示如何测试一个基础 UI 组件
 */

import { render, screen } from '../../tests/test-utils'
import { userEvent } from '../../tests/test-utils'

// 示例 Button 组件（实际使用时应该从组件库导入）
interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}

function Button({ children, onClick, disabled, variant = 'primary' }: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
      data-testid="button"
    >
      {children}
    </button>
  )
}

describe('Button Component', () => {
  describe('Rendering', () => {
    it('should render with children text', () => {
      render(<Button>Click Me</Button>)

      const button = screen.getByRole('button', { name: /click me/i })
      expect(button).toBeInTheDocument()
    })

    it('should apply primary variant by default', () => {
      render(<Button>Submit</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('btn btn-primary')
    })

    it('should apply secondary variant when specified', () => {
      render(<Button variant="secondary">Cancel</Button>)

      const button = screen.getByRole('button')
      expect(button).toHaveClass('btn btn-secondary')
    })

    it('should render in disabled state', () => {
      render(<Button disabled>Disabled</Button>)

      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })
  })

  describe('User Interactions', () => {
    it('should call onClick handler when clicked', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()

      render(<Button onClick={handleClick}>Click Me</Button>)

      const button = screen.getByRole('button')
      await user.click(button)

      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should not call onClick when disabled', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()

      render(
        <Button onClick={handleClick} disabled>
          Disabled
        </Button>
      )

      const button = screen.getByRole('button')
      await user.click(button)

      expect(handleClick).not.toHaveBeenCalled()
    })

    it('should handle multiple clicks', async () => {
      const handleClick = jest.fn()
      const user = userEvent.setup()

      render(<Button onClick={handleClick}>Click Me</Button>)

      const button = screen.getByRole('button')
      await user.click(button)
      await user.click(button)
      await user.click(button)

      expect(handleClick).toHaveBeenCalledTimes(3)
    })
  })

  describe('Edge Cases', () => {
    it('should handle missing onClick handler gracefully', async () => {
      const user = userEvent.setup()

      render(<Button>No Handler</Button>)

      const button = screen.getByRole('button')

      // Should not throw error
      await expect(user.click(button)).resolves.not.toThrow()
    })

    it('should render with complex children', () => {
      render(
        <Button>
          <span>Icon</span>
          <span>Text</span>
        </Button>
      )

      expect(screen.getByText('Icon')).toBeInTheDocument()
      expect(screen.getByText('Text')).toBeInTheDocument()
    })
  })
})
