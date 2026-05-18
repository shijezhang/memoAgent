import { Fragment } from 'react'
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react'
import { X } from 'lucide-react'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </TransitionChild>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <TransitionChild
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <DialogPanel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <DialogTitle as="h3" className="text-lg font-semibold text-gray-900 dark:text-white">
                    设置
                  </DialogTitle>
                  <button
                    onClick={onClose}
                    className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                    aria-label="关闭"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Model Info */}
                  <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">当前模型</div>
                    <div className="text-gray-900 dark:text-white">DeepSeek</div>
                  </div>

                  {/* Placeholder for future settings */}
                  <div className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                    更多设置选项即将推出...
                  </div>
                </div>

                <div className="mt-6">
                  <button
                    type="button"
                    className="w-full px-4 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 rounded-lg transition-colors"
                    onClick={onClose}
                  >
                    完成
                  </button>
                </div>
              </DialogPanel>
            </TransitionChild>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}

export default SettingsModal
